#!/usr/bin/env python3
"""
集成提示词生成器 - 整合场景规则与现有提示词系统
Integrated Prompt Generator - Integrate scenario rules with existing prompt system

版本: 1.0.0
创建时间: 2026-01-23
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.legal_world_model.scenario_identifier import ScenarioContext
from core.legal_world_model.scenario_rule_retriever import ScenarioRule

logger = logging.getLogger(__name__)


@dataclass
class IntegratedPrompt:
    """
    集成提示词数据类

    包含了场景规则、L1-L4角色、专家人设、Lyra优化等所有信息
    """

    system_prompt: str
    user_prompt: str

    # 场景规则信息
    scenario_rule_id: str
    scenario_domain: str
    scenario_task_type: str

    # 代理配置
    agent_level: str
    expert_config: dict[str, Any]
    # 处理规则和工作流
    processing_rules: list[str]
    workflow_steps: list[dict[str, Any]]
    # 法律依据和参考案例
    legal_basis: list[dict[str, Any]]
    reference_cases: list[dict[str, Any]]
    # 优化信息
    lyra_optimized: bool = False
    lyra_focus: list[str] = field(default_factory=list)
    confidence: float = 0.0

    # 元数据
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "scenario_rule_id": self.scenario_rule_id,
            "scenario_domain": self.scenario_domain,
            "scenario_task_type": self.scenario_task_type,
            "agent_level": self.agent_level,
            "expert_config": self.expert_config,
            "processing_rules": self.processing_rules,
            "workflow_steps": self.workflow_steps,
            "legal_basis": self.legal_basis,
            "reference_cases": self.reference_cases,
            "lyra_optimized": self.lyra_optimized,
            "lyra_focus": self.lyra_focus,
            "confidence": self.confidence,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }

    def get_summary(self) -> str:
        """获取提示词摘要"""
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║              集成提示词摘要                                  ║
╚═══════════════════════════════════════════════════════════╝

📊 场景信息:
  领域: {self.scenario_domain}
  任务: {self.scenario_task_type}
  规则ID: {self.scenario_rule_id}

🤖 代理配置:
  角色等级: {self.agent_level}
  专家配置: {self.expert_config.get('primary_expert', 'N/A')}

📋 处理规则: {len(self.processing_rules)} 条
🔄 工作流步骤: {len(self.workflow_steps)} 步
📚 法律依据: {len(self.legal_basis)} 条
⚖️  参考案例: {len(self.reference_cases)} 个

✨ 优化信息:
  Lyra优化: {'是' if self.lyra_optimized else '否'}
  优化重点: {', '.join(self.lyra_focus) if self.lyra_focus else '无'}
  置信度: {self.confidence:.2%}

📝 提示词长度:
  System: {len(self.system_prompt)} 字符
  User: {len(self.user_prompt)} 字符

⏰ 生成时间: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return summary


class IntegratedPromptGenerator:
    """
    集成提示词生成器

    整合:
    - 场景规则(ScenarioRule)
    - L1-L4代理角色(UnifiedPromptManager)
    - Lyra优化系统
    - 专家人设(ExpertPromptGenerator)
    """

    def __init__(
        self,
        unified_prompt_manager=None,
        dynamic_prompt_generator=None,
        expert_prompt_generator=None,
    ):
        """
        初始化集成提示词生成器

        Args:
            unified_prompt_manager: UnifiedPromptManager实例
            dynamic_prompt_generator: DynamicPromptGenerator实例(可选)
            expert_prompt_generator: ExpertPromptGenerator实例(可选)
        """
        self.unified_prompt_manager = unified_prompt_manager
        self.dynamic_prompt_generator = dynamic_prompt_generator
        self.expert_prompt_generator = expert_prompt_generator

    def generate(
        self,
        scenario_context: ScenarioContext,
        scenario_rule: ScenarioRule,
        user_input: str,
        additional_variables: dict[str, Any] | None = None,
    ) -> IntegratedPrompt:
        """
        生成集成提示词

        Args:
            scenario_context: 场景上下文
            scenario_rule: 场景规则
            user_input: 用户输入
            additional_variables: 额外变量

        Returns:
            IntegratedPrompt: 集成提示词对象
        """
        logger.info(f"🔧 生成集成提示词: {scenario_rule.rule_id}")

        # 1. 合并变量
        all_variables = {**scenario_context.extracted_variables, **(additional_variables or {})}

        logger.info(f"  可用变量: {list(all_variables.keys())}")

        # 2. 替换场景规则模板中的变量
        system_prompt, user_prompt = scenario_rule.substitute_variables(all_variables)

        # 3. 注入L1-L4角色定义
        agent_level = scenario_rule.agent_level
        agent_role_prompt = self._get_agent_role_prompt(agent_level)

        if agent_role_prompt:
            system_prompt = f"{agent_role_prompt}\n\n{system_prompt}"
            logger.info(f"  ✅ 注入L1-L4角色: {agent_level}")

        # 4. 注入专家人设
        expert_config = scenario_rule.expert_config
        if expert_config:
            expert_prompt = self._get_expert_prompt(expert_config)
            if expert_prompt:
                system_prompt = f"{expert_prompt}\n\n{system_prompt}"
                logger.info(f"  ✅ 注入专家人设: {expert_config.get('primary_expert', 'N/A')}")

        # 5. 添加处理规则
        if scenario_rule.processing_rules:
            rules_section = "\n## 📋 处理规则\n\n"
            for i, rule in enumerate(scenario_rule.processing_rules, 1):
                rules_section += f"{i}. {rule}\n"
            system_prompt += f"\n{rules_section}"

        # 6. 添加工作流步骤
        if scenario_rule.workflow_steps:
            workflow_section = "\n## 🔄 工作流程\n\n"
            for step in scenario_rule.workflow_steps:
                workflow_section += f"**步骤{step['step']}**: {step['name']}\n"
            system_prompt += f"\n{workflow_section}"

        # 7. 添加法律依据
        if scenario_rule.legal_basis:
            legal_section = "\n## 📚 法律依据\n\n"
            for basis in scenario_rule.legal_basis[:5]:  # 限制前5条
                legal_section += f"- {basis}\n"
            system_prompt += f"\n{legal_section}"

        # 8. Lyra优化(如果启用)
        lyra_optimized = False
        if scenario_rule.lyra_optimization and self.unified_prompt_manager:
            try:
                # 优化system prompt
                system_prompt = self.unified_prompt_manager.optimize_prompt(
                    system_prompt, f"scenario_{scenario_rule.domain}_{scenario_rule.task_type}"
                )
                lyra_optimized = True
                logger.info("  ✅ Lyra优化完成")
            except Exception as e:
                logger.warning(f"  ⚠️ Lyra优化失败: {e}")

        # 9. 构建集成提示词对象
        integrated_prompt = IntegratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            scenario_rule_id=scenario_rule.rule_id,
            scenario_domain=scenario_rule.domain,
            scenario_task_type=scenario_rule.task_type,
            agent_level=agent_level,
            expert_config=expert_config,
            processing_rules=scenario_rule.processing_rules,
            workflow_steps=scenario_rule.workflow_steps,
            legal_basis=scenario_rule.legal_basis,
            reference_cases=scenario_rule.reference_cases,
            lyra_optimized=lyra_optimized,
            lyra_focus=scenario_rule.lyra_focus,
            confidence=scenario_context.confidence,
            metadata={
                "user_input_length": len(user_input),
                "variables_used": list(all_variables.keys()),
                "generation_method": "integrated",
            },
        )

        logger.info("✅ 集成提示词生成完成")

        return integrated_prompt

    def _get_agent_role_prompt(self, agent_level: str) -> str | None:
        """
        获取代理角色提示词

        Args:
            agent_level: 代理等级 (L1/L2/L3/L4)

        Returns:
            str: 代理角色提示词,如果未找到则返回None
        """
        if not self.unified_prompt_manager:
            logger.warning("⚠️ UnifiedPromptManager未初始化,跳过L1-L4角色注入")
            return None

        try:
            # 映射agent_level到agent_name
            agent_mapping = {
                "L1": "xiaonuo",
                "L2": "xiaona",
                "L3": "professional_agent",
                "L4": "team_agent",
            }

            agent_name = agent_mapping.get(agent_level, "xiaona")

            # 导入PromptFormat
            from core.prompts.unified_prompt_manager import PromptFormat

            # 使用UnifiedPromptManager加载提示词
            role_prompt = self.unified_prompt_manager.load_prompt(agent_name, PromptFormat.MARKDOWN)

            if role_prompt:
                logger.info(f"  📋 加载代理角色: {agent_name} ({agent_level})")

            return role_prompt

        except Exception as e:
            logger.warning(f"⚠️ 加载代理角色提示词失败: {e}")
            return None

    def _get_expert_prompt(self, expert_config: dict[str, Any]) -> str | None:
        """
        获取专家提示词

        Args:
            expert_config: 专家配置

        Returns:
            str: 专家提示词,如果未找到则返回None
        """
        if not self.expert_prompt_generator:
            logger.warning("⚠️ ExpertPromptGenerator未初始化,跳过专家人设注入")
            return None

        try:
            primary_expert = expert_config.get("primary_expert")
            supporting_experts = expert_config.get("supporting_experts", [])
            collaboration_mode = expert_config.get("collaboration_mode", "single")

            if collaboration_mode == "single" and primary_expert:
                # 单专家模式
                expert_prompt = self.expert_prompt_generator.generate_expert_prompt(
                    primary_expert, context={}
                )

                if expert_prompt:
                    logger.info(f"  👨‍🔬 加载专家: {primary_expert}")

                return expert_prompt

            elif collaboration_mode == "sequential" and supporting_experts:
                # 多专家协作模式
                team_prompt = self.expert_prompt_generator.generate_team_prompt(
                    [primary_expert, *supporting_experts], context={}
                )

                if team_prompt:
                    logger.info(f"  👥 加载专家团队: {primary_expert} + {len(supporting_experts)}")

                return team_prompt

            return None

        except Exception as e:
            logger.warning(f"⚠️ 加载专家提示词失败: {e}")
            return None

    def generate_with_legal_context(
        self,
        scenario_context: ScenarioContext,
        scenario_rule: ScenarioRule,
        user_input: str,
        legal_basis: list[dict[str, Any]],        reference_cases: list[dict[str, Any]],        additional_variables: dict[str, Any] | None = None,
    ) -> IntegratedPrompt:
        """
        生成包含法律上下文的集成提示词

        Args:
            scenario_context: 场景上下文
            scenario_rule: 场景规则
            user_input: 用户输入
            legal_basis: 法律依据
            reference_cases: 参考案例
            additional_variables: 额外变量

        Returns:
            IntegratedPrompt: 集成提示词对象
        """
        # 生成基础提示词
        integrated_prompt = self.generate(
            scenario_context=scenario_context,
            scenario_rule=scenario_rule,
            user_input=user_input,
            additional_variables=additional_variables,
        )

        # 添加法律依据到system prompt
        if legal_basis:
            legal_section = "\n## 📚 相关法律依据\n\n"
            for basis in legal_basis[:5]:
                legal_section += f"### {basis['title']}\n"
                legal_section += f"{basis['content'][:200]}...\n\n"
            integrated_prompt.system_prompt += legal_section

        # 添加参考案例到system prompt
        if reference_cases:
            case_section = "\n## ⚖️  参考案例\n\n"
            for case in reference_cases[:3]:
                case_section += f"### {case['title']}\n"
                case_section += f"- 案号: {case.get('case_number', 'N/A')}\n"
                case_section += f"- 法院: {case.get('court', 'N/A')}\n"
                case_section += f"- 要旨: {case.get('result', 'N/A')[:100]}...\n\n"
            integrated_prompt.system_prompt += case_section

        # 更新metadata
        integrated_prompt.metadata["legal_basis_count"] = len(legal_basis)
        integrated_prompt.metadata["reference_cases_count"] = len(reference_cases)

        # 更新legal_basis和reference_cases字段
        integrated_prompt.legal_basis = legal_basis
        integrated_prompt.reference_cases = reference_cases

        return integrated_prompt


# 便捷函数
def generate_integrated_prompt(
    scenario_context: ScenarioContext,
    scenario_rule: ScenarioRule,
    user_input: str,
    unified_prompt_manager=None,
    additional_variables: dict[str, Any] | None = None,
) -> IntegratedPrompt:
    """
    便捷函数:生成集成提示词

    Args:
        scenario_context: 场景上下文
        scenario_rule: 场景规则
        user_input: 用户输入
        unified_prompt_manager: UnifiedPromptManager实例
        additional_variables: 额外变量

    Returns:
        IntegratedPrompt: 集成提示词对象
    """
    generator = IntegratedPromptGenerator(unified_prompt_manager=unified_prompt_manager)

    return generator.generate(
        scenario_context=scenario_context,
        scenario_rule=scenario_rule,
        user_input=user_input,
        additional_variables=additional_variables,
    )
