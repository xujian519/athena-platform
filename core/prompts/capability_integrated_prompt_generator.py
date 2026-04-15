#!/usr/bin/env python3
from __future__ import annotations
"""
增强的集成提示词生成器(支持能力调用)
Enhanced Integrated Prompt Generator with Capability Invocation

在原有集成提示词生成器基础上,添加动态能力调用功能
"""

import logging
from typing import Any

from jinja2 import Template

from core.capabilities.capability_invoker import CapabilityInvoker
from core.capabilities.capability_orchestrator import CapabilityOrchestrator
from core.legal_world_model.scenario_identifier_optimized import ScenarioContext
from core.legal_world_model.scenario_rule_retriever_optimized import ScenarioRule
from core.prompts.integrated_prompt_generator import IntegratedPrompt, IntegratedPromptGenerator

logger = logging.getLogger(__name__)


class CapabilityIntegratedPromptGenerator(IntegratedPromptGenerator):
    """
    支持能力调用的集成提示词生成器

    在原有生成器基础上添加:
    - 自动调用能力
    - 结果注入提示词
    - 能力编排
    """

    def __init__(
        self,
        unified_prompt_manager=None,
        dynamic_prompt_generator=None,
        expert_prompt_generator=None,
    ):
        """初始化"""
        super().__init__(unified_prompt_manager, dynamic_prompt_generator, expert_prompt_generator)

        # 初始化能力调用组件
        self.capability_invoker = CapabilityInvoker()
        self.capability_orchestrator = CapabilityOrchestrator(self.capability_invoker)

        logger.info("✅ 能力集成提示词生成器初始化完成")

    async def generate_with_capabilities(
        self,
        scenario_context: ScenarioContext,
        scenario_rule: ScenarioRule,
        user_input: str,
        additional_variables: dict[str, Any] | None = None,
    ) -> IntegratedPrompt:
        """
        生成带能力调用的集成提示词

        Args:
            scenario_context: 场景上下文
            scenario_rule: 场景规则(支持能力调用配置)
            user_input: 用户输入
            additional_variables: 额外变量

        Returns:
            集成提示词
        """
        logger.info("🔧 生成带能力调用的集成提示词")

        # 1. 合并变量
        all_variables = {**scenario_context.extracted_variables, **(additional_variables or {})}

        # 2. 检查是否有能力调用配置
        capability_invocations = getattr(scenario_rule, "capability_invocations", None)

        capability_results = {}

        if capability_invocations:
            logger.info(f"  📋 执行能力调用: {len(capability_invocations)}个")

            try:
                # 执行能力调用
                capability_results = await self.capability_orchestrator.execute_workflow(
                    capability_invocations, all_variables
                )

                logger.info(f"  ✅ 能力调用完成: {list(capability_results.keys())}")

                # 将能力结果合并到变量中
                all_variables.update(capability_results)

                # 添加元数据
                for key, value in capability_results.items():
                    if isinstance(value, list):
                        logger.info(f"    - {key}: {len(value)}项")
                    elif isinstance(value, dict):
                        logger.info(f"    - {key}: {list(value.keys())}")
                    else:
                        logger.info(f"    - {key}: {type(value).__name__}")

            except Exception as e:
                logger.error(f"  ❌ 能力调用失败: {e}")
                # 继续执行,不中断提示词生成

        # 3. 替换提示词模板
        system_prompt, user_prompt = scenario_rule.substitute_variables(all_variables)

        # 4. 注入L1-L4角色
        agent_level = scenario_rule.agent_level
        agent_role_prompt = self._get_agent_role_prompt(agent_level)

        if agent_role_prompt:
            system_prompt = f"{agent_role_prompt}\n\n{system_prompt}"

        # 5. 注入专家人设
        expert_config = scenario_rule.expert_config
        if expert_config:
            expert_prompt = self._get_expert_prompt(expert_config)
            if expert_prompt:
                system_prompt = f"{expert_prompt}\n\n{system_prompt}"

        # 6. 添加处理规则
        if scenario_rule.processing_rules:
            rules_section = "\n## 📋 处理规则\n\n"
            for i, rule in enumerate(scenario_rule.processing_rules, 1):
                rules_section += f"{i}. {rule}\n"
            system_prompt += f"\n{rules_section}"

        # 7. 添加工作流步骤
        if scenario_rule.workflow_steps:
            workflow_section = "\n## 🔄 工作流程\n\n"
            for step in scenario_rule.workflow_steps:
                workflow_section += f"**步骤{step['step']}**: {step['name']}\n"
            system_prompt += f"\n{workflow_section}"

        # 8. 如果有专门的能力结果模板,进行注入
        capability_prompt_template = getattr(scenario_rule, "capability_prompt_template", None)

        if capability_prompt_template and capability_results:
            capability_section = self._render_capability_template(
                capability_prompt_template, capability_results
            )
            system_prompt += f"\n{capability_section}"

        # 9. Lyra优化
        lyra_optimized = False
        if scenario_rule.lyra_optimization and self.unified_prompt_manager:
            try:
                system_prompt = self.unified_prompt_manager.optimize_prompt(
                    system_prompt, f"scenario_{scenario_rule.domain}_{scenario_rule.task_type}"
                )
                lyra_optimized = True
            except Exception as e:
                logger.warning(f"⚠️ Lyra优化失败: {e}")

        # 10. 构建集成提示词对象
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
                **scenario_context.extracted_variables,
                "capability_results": list(capability_results.keys()),
                "capability_count": len(capability_results),
                "generation_method": "integrated_with_capabilities",
            },
        )

        logger.info("✅ 带能力调用的集成提示词生成完成")

        return integrated_prompt

    def _render_capability_template(self, template_str: str, results: dict[str, Any]) -> str:
        """
        渲染能力结果模板

        Args:
            template_str: 模板字符串(支持Jinja2语法)
            results: 能力结果

        Returns:
            渲染后的文本
        """
        try:
            template = Template(template_str)
            return template.render(**results)
        except Exception as e:
            logger.warning(f"⚠️ 模板渲染失败: {e}")
            # 简单的回退渲染
            return self._simple_render(template_str, results)

    def _simple_render(self, template_str: str, results: dict[str, Any]) -> str:
        """简单的模板渲染(回退方案)"""
        rendered = template_str

        # 简单的变量替换
        for key, value in results.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))

            # 处理条件块
            if_block_start = f"{{{{#{key}}}}}"
            if_block_end = f"{{{{/{key}}}}}"
            if value:
                # 移除条件标记
                rendered = rendered.replace(if_block_start, "")
                rendered = rendered.replace(if_block_end, "")
            else:
                # 移除整个条件块
                start = rendered.find(if_block_start)
                if start != -1:
                    end = rendered.find(if_block_end, start)
                    if end != -1:
                        rendered = rendered[:start] + rendered[end + len(if_block_end) :]

        return rendered


# 便捷函数
async def generate_prompt_with_capabilities(
    scenario_context: ScenarioContext,
    scenario_rule: ScenarioRule,
    user_input: str,
    unified_prompt_manager=None,
    additional_variables: dict[str, Any] | None = None,
) -> IntegratedPrompt:
    """
    便捷的带能力调用的提示词生成函数

    Args:
        scenario_context: 场景上下文
        scenario_rule: 场景规则
        user_input: 用户输入
        unified_prompt_manager: 统一提示词管理器
        additional_variables: 额外变量

    Returns:
        集成提示词
    """
    generator = CapabilityIntegratedPromptGenerator(unified_prompt_manager=unified_prompt_manager)

    return await generator.generate_with_capabilities(
        scenario_context=scenario_context,
        scenario_rule=scenario_rule,
        user_input=user_input,
        additional_variables=additional_variables,
    )
