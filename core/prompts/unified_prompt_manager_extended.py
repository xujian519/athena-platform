#!/usr/bin/env python3
"""
扩展的统一提示词管理器 - 集成场景规则
Extended Unified Prompt Manager - Integrated with Scenario Rules

版本: 1.0.0
创建时间: 2026-01-23

这个模块扩展了原有的UnifiedPromptManager,添加了场景感知的提示词生成能力。
"""

import logging
from typing import Any, Dict, Optional

from core.legal_world_model.scenario_identifier_optimized import ScenarioContext, ScenarioIdentifierOptimized as ScenarioIdentifier
from core.legal_world_model.scenario_rule_retriever_optimized import ScenarioRule, ScenarioRuleRetrieverOptimized as ScenarioRuleRetriever
from core.prompts.integrated_prompt_generator import IntegratedPromptGenerator
from core.prompts.unified_prompt_manager import UnifiedPromptManager

logger = logging.getLogger(__name__)


class SimpleNeo4jManager:
    """简单的Neo4j管理器,用于提示词管理器"""

    def __init__(self):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "athena_neo4j_2024")
        )

    def neo4j_session(self):
        """返回Neo4j会话上下文管理器"""
        return self.driver.session()

    def session(self):
        """返回Neo4j会话上下文管理器（兼容方法）"""
        return self.driver.session()

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


class ExtendedUnifiedPromptManager(UnifiedPromptManager):
    """
    扩展的统一提示词管理器

    在原有UnifiedPromptManager基础上,添加:
    - 场景识别
    - 场景规则检索
    - 集成提示词生成
    """

    def __init__(self, *args, **kwargs):
        """
        初始化扩展的统一提示词管理器

        接受与UnifiedPromptManager相同的参数
        """
        super().__init__(*args, **kwargs)

        # 初始化数据库管理器
        if not hasattr(self, 'db_manager') or self.db_manager is None:
            self.db_manager = SimpleNeo4jManager()

        # 初始化场景相关组件
        self.scenario_identifier = ScenarioIdentifier()
        self.scenario_rule_retriever = ScenarioRuleRetriever(self.db_manager)
        self.integrated_prompt_generator = IntegratedPromptGenerator(
            unified_prompt_manager=self,
            expert_prompt_generator=getattr(self, "expert_generator", None),
        )

    def generate_scenario_based_prompt(
        self,
        user_input: str,
        scenario_context: ScenarioContext | None = None,
        additional_context: dict[str, Any] | None = None,
        enable_l1_l4: bool = True,
        enable_expert: bool = True,
        enable_lyra: bool = True,
    ) -> dict[str, Any]:
        """
        基于场景生成集成提示词

        这是核心方法,整合了场景识别、规则检索和提示词生成

        Args:
            user_input: 用户输入
            scenario_context: 预识别的场景上下文(可选,如果不提供则自动识别)
            additional_context: 额外上下文信息
            enable_l1_l4: 是否启用L1-L4角色注入
            enable_expert: 是否启用专家人设注入
            enable_lyra: 是否启用Lyra优化

        Returns:
            Dict: 包含提示词和元数据的字典
        """
        logger.info(f"🎯 生成场景感知提示词: {user_input[:100]}...")

        # 1. 场景识别(如果未提供)
        if not scenario_context:
            scenario_context = self.scenario_identifier.identify_scenario(
                user_input, additional_context
            )

        logger.info(
            f"  场景: {scenario_context.domain.value}/"
            f"{scenario_context.task_type.value}/"
            f"{scenario_context.phase.value}"
        )

        # 2. 检索场景规则
        scenario_rule = self.scenario_rule_retriever.retrieve_rule_with_relations(
            domain=scenario_context.domain.value,
            task_type=scenario_context.task_type.value,
            phase=scenario_context.phase.value if scenario_context.phase.value != "other" else None,
        )

        if not scenario_rule:
            logger.warning("⚠️ 未找到场景规则,使用默认提示词")
            return self._generate_default_prompt(user_input, scenario_context)

        logger.info(f"  规则: {scenario_rule.rule_id}")

        # 3. 临时禁用不需要的集成
        original_unified_manager = self.integrated_prompt_generator.unified_prompt_manager
        original_expert_generator = self.integrated_prompt_generator.expert_prompt_generator

        if not enable_l1_l4:
            self.integrated_prompt_generator.unified_prompt_manager = None

        if not enable_expert:
            self.integrated_prompt_generator.expert_prompt_generator = None

        # 4. 如果禁用Lyra,临时修改规则
        original_lyra_setting = scenario_rule.lyra_optimization
        if not enable_lyra:
            scenario_rule.lyra_optimization = False

        # 5. 生成集成提示词
        try:
            integrated_prompt = self.integrated_prompt_generator.generate(
                scenario_context=scenario_context,
                scenario_rule=scenario_rule,
                user_input=user_input,
            )
        finally:
            # 恢复原始设置
            self.integrated_prompt_generator.unified_prompt_manager = original_unified_manager
            self.integrated_prompt_generator.expert_prompt_generator = original_expert_generator
            scenario_rule.lyra_optimization = original_lyra_setting

        # 6. 构建返回结果
        result = {
            "system_prompt": integrated_prompt.system_prompt,
            "user_prompt": integrated_prompt.user_prompt,
            # 场景信息
            "scenario": {
                "domain": integrated_prompt.scenario_domain,
                "task_type": integrated_prompt.scenario_task_type,
                "rule_id": integrated_prompt.scenario_rule_id,
                "confidence": integrated_prompt.confidence,
            },
            # 配置信息
            "config": {
                "agent_level": integrated_prompt.agent_level,
                "expert_config": integrated_prompt.expert_config,
                "processing_rules": integrated_prompt.processing_rules,
                "workflow_steps": integrated_prompt.workflow_steps,
            },
            # 法律依据和参考案例
            "legal_context": {
                "legal_basis": integrated_prompt.legal_basis,
                "reference_cases": integrated_prompt.reference_cases,
            },
            # 优化信息
            "optimization": {
                "lyra_optimized": integrated_prompt.lyra_optimized,
                "lyra_focus": integrated_prompt.lyra_focus,
            },
            # 元数据
            "metadata": integrated_prompt.metadata,
        }

        logger.info("✅ 场景感知提示词生成完成")

        return result

    def _generate_default_prompt(
        self, user_input: str, scenario_context: ScenarioContext
    ) -> dict[str, Any]:
        """生成默认提示词(当未找到场景规则时)"""
        logger.info("使用默认提示词生成")

        # 使用现有的L2代理作为默认
        from core.prompts.unified_prompt_manager import PromptFormat

        default_system = self.load_prompt("xiaona", PromptFormat.MARKDOWN)

        result = {
            "system_prompt": default_system,
            "user_prompt": user_input,
            "scenario": {
                "domain": scenario_context.domain.value,
                "task_type": scenario_context.task_type.value,
                "rule_id": "default",
                "confidence": scenario_context.confidence,
            },
            "config": {
                "agent_level": "L2",
                "expert_config": {},
                "processing_rules": [],
                "workflow_steps": [],
            },
            "legal_context": {"legal_basis": [], "reference_cases": []},
            "optimization": {"lyra_optimized": False, "lyra_focus": []},
            "metadata": {
                "generation_method": "default",
                "fallback_reason": "no_scenario_rule_found",
            },
        }

        return result

    def process_query_with_scenario(
        self, user_query: str, additional_context: dict[str, Any] | None = None, **options
    ) -> dict[str, Any]:
        """
        使用场景感知的方式处理查询

        这是一个高级方法,整合了场景识别、规则检索、提示词生成和结果处理

        Args:
            user_query: 用户查询
            additional_context: 额外上下文
            **options: 额外选项

        Returns:
            Dict: 包含提示词和场景信息的完整结果
        """
        logger.info(f"🚀 处理场景感知查询: {user_query[:100]}...")

        # 1. 生成场景感知提示词
        prompt_result = self.generate_scenario_based_prompt(
            user_input=user_query, additional_context=additional_context, **options
        )

        # 2. 添加处理建议
        suggestions = self._generate_processing_suggestions(prompt_result)

        # 3. 构建完整结果
        result = {**prompt_result, "suggestions": suggestions, "ready_for_llm": True}

        logger.info("✅ 场景感知查询处理完成")

        return result

    def _generate_processing_suggestions(self, prompt_result: dict[str, Any]) -> dict[str, Any]:
        """生成处理建议"""
        suggestions = {"next_steps": [], "considerations": [], "workflow": []}

        # 基于工作流步骤生成建议
        workflow_steps = prompt_result.get("config", {}).get("workflow_steps", [])
        if workflow_steps:
            suggestions["workflow"] = [
                f"步骤{step['step']}: {step['name']}" for step in workflow_steps
            ]
            suggestions["next_steps"].append(f"按照{len(workflow_steps)}步工作流程处理")

        # 基于处理规则生成建议
        processing_rules = prompt_result.get("config", {}).get("processing_rules", [])
        if processing_rules:
            suggestions["considerations"].extend(processing_rules)

        # 基于法律依据生成建议
        legal_basis = prompt_result.get("legal_context", {}).get("legal_basis", [])
        if legal_basis:
            suggestions["considerations"].append(f"参考{len(legal_basis)}条法律依据")

        return suggestions

    def list_available_scenarios(self, domain: str | None = None) -> list:
        """
        列出可用的场景

        Args:
            domain: 可选,过滤特定领域

        Returns:
            list: 场景列表
        """
        return self.scenario_rule_retriever.list_available_scenarios(domain)

    def get_scenario_rule(
        self, domain: str, task_type: str, phase: str | None = None
    ) -> ScenarioRule | None:
        """
        获取场景规则

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段

        Returns:
            ScenarioRule: 规则对象或None
        """
        return self.scenario_rule_retriever.retrieve_rule_with_relations(domain, task_type, phase)


# 便捷函数
def create_scenario_aware_prompt_manager(*args, **kwargs) -> ExtendedUnifiedPromptManager:
    """
    创建场景感知的提示词管理器

    Args:
        *args: 传递给UnifiedPromptManager的参数
        **kwargs: 传递给UnifiedPromptManager的关键字参数

    Returns:
        ExtendedUnifiedPromptManager: 场景感知的提示词管理器实例
    """
    return ExtendedUnifiedPromptManager(*args, **kwargs)
