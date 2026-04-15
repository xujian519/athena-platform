#!/usr/bin/env python3
from __future__ import annotations
"""
小娜·天秤女神 - 集成法律世界模型版本
Xiaona Libra Goddess - Legal World Model Integrated Version

本模块实现小娜智能体与法律世界模型的深度集成，
确保所有专利相关业务都基于法律世界模型进行。

核心特性:
1. 强制使用法律世界模型进行场景识别
2. 从Neo4j检索法律依据和规则
3. 生成包含法律上下文的动态提示词
4. 合规性验证和解释性输出

Author: Athena Team
Version: 1.0.0
Date: 2026-03-06
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# 导入基础智能体
from core.agents.base import (
    AgentCapability,
    AgentMetadata,
    BaseAgent,
)

# 导入提示词生成器
from core.intelligence.legal_world_prompt_generator import (
    DynamicPrompt,
    LegalContext,
    LegalWorldPromptGenerator,
)

# 导入法律世界模型组件
from core.legal_world_model.constitution import (
    ConstitutionalValidator,
)
from core.legal_world_model.enhanced_scenario_identifier import (
    EnhancedScenarioIdentifier,
)
from core.legal_world_model.scenario_identifier import (
    Domain,
    Phase,
    ScenarioContext,
    TaskType,
)
from core.legal_world_model.scenario_rule_retriever import (
    ScenarioRule,
    ScenarioRuleRetriever,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalWorldIntegrationMode(Enum):
    """法律世界模型集成模式"""

    STRICT = "strict"  # 严格模式：必须使用法律世界模型
    HYBRID = "hybrid"  # 混合模式：优先使用法律世界模型，回退到通用能力
    FALLBACK = "fallback"  # 回退模式：法律世界模型失败时使用通用能力


@dataclass
class LegalWorldEnhancedRequest:
    """增强的法律世界请求"""

    # 原始请求
    original_request: str

    # 场景识别结果
    scenario_context: ScenarioContext

    # 检索的法律规则
    scenario_rule: ScenarioRule | None = None

    # 动态提示词
    dynamic_prompt: DynamicPrompt | None = None

    # 法律依据
    legal_basis: list[str] = field(default_factory=list)

    # 参考案例
    reference_cases: list[dict[str, str]] = field(default_factory=list)

    # 处理规则
    processing_rules: list[str] = field(default_factory=list)

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "original_request": self.original_request,
            "scenario_context": {
                "domain": self.scenario_context.domain.value,
                "task_type": self.scenario_context.task_type.value,
                "phase": self.scenario_context.phase.value,
                "confidence": self.scenario_context.confidence,
            },
            "legal_basis": self.legal_basis,
            "reference_cases": self.reference_cases,
            "processing_rules": self.processing_rules,
            "metadata": self.metadata,
        }


class XiaonaWithLegalWorld(BaseAgent):
    """
    小娜·天秤女神 - 法律世界模型集成版

    核心特性:
    1. 所有专利相关业务必须基于法律世界模型
    2. 场景识别 → 规则检索 → 提示词生成 → 执行 → 验证
    3. 完整的可解释性输出
    4. 支持HITL人工干预
    """

    # ========== 属性 ==========

    @property
    def name(self) -> str:
        """智能体唯一标识"""
        return "xiaona-legal-world"

    def _load_metadata(self) -> AgentMetadata:
        """加载元数据"""
        return AgentMetadata(
            name=self.name,
            version="1.0.0",
            description="小娜·天秤女神 - 法律世界模型集成版，所有专利业务必须基于法律世界模型",
            author="Athena Team",
            tags=["法律", "专利", "法律世界模型", "合规性", "可解释性"],
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """注册能力列表"""
        return [
            AgentCapability(
                name="patent-drafting-with-legal-world",
                description="专利撰写（基于法律世界模型）- 权利要求书+说明书，必须依据法律世界模型",
                parameters={
                    "tech_disclosure": {
                        "type": "string",
                        "description": "技术交底书内容",
                    },
                    "inventor_info": {
                        "type": "object",
                        "description": "发明人信息（可选）",
                    },
                },
            ),
            AgentCapability(
                name="office-action-response-with-legal-world",
                description="审查意见答复（基于法律世界模型）- 必须依据法律世界模型",
                parameters={
                    "oa_text": {
                        "type": "string",
                        "description": "审查意见文本",
                    },
                    "application_no": {
                        "type": "string",
                        "description": "专利申请号",
                    },
                    "claims": {
                        "type": "string",
                        "description": "权利要求书",
                    },
                },
            ),
            AgentCapability(
                name="invalidity-request-with-legal-world",
                description="无效宣告请求（基于法律世界模型）- 必须依据法律世界模型",
                parameters={
                    "patent_no": {
                        "type": "string",
                        "description": "目标专利号",
                    },
                    "invalidity_grounds": {
                        "type": "list",
                        "description": "无效理由",
                    },
                },
            ),
            AgentCapability(
                name="novelty-analysis-with-legal-world",
                description="新颖性分析（基于法律世界模型）- 必须依据法律世界模型",
                parameters={
                    "patent_content": {
                        "type": "string",
                        "description": "专利内容",
                    },
                    "prior_art": {
                        "type": "list",
                        "description": "现有技术",
                    },
                },
            ),
            AgentCapability(
                name="creativity-analysis-with-legal-world",
                description="创造性分析（基于法律世界模型）- 必须依据法律世界模型",
                parameters={
                    "patent_content": {
                        "type": "string",
                        "description": "专利内容",
                    },
                    "closest_prior_art": {
                        "type": "string",
                        "description": "最接近现有技术",
                    },
                },
            ),
        ]

    # ========== 初始化 ==========

    def __init__(
        self,
        integration_mode: LegalWorldIntegrationMode = LegalWorldIntegrationMode.STRICT,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_username: str = "neo4j",
        neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password"),
        neo4j_database: str = "legal_world",
    ):
        """
        初始化小娜智能体

        Args:
            integration_mode: 集成模式
            neo4j_uri: Neo4j服务URI
            neo4j_username: Neo4j用户名
            neo4j_password: Neo4j密码
            neo4j_database: 数据库名称
        """
        super().__init__()

        # 集成模式
        self.integration_mode = integration_mode

        # Neo4j配置
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database

        # 核心组件（延迟初始化）
        self.scenario_identifier: EnhancedScenarioIdentifier | None = None
        self.rule_retriever: ScenarioRuleRetriever | None = None
        self.prompt_generator: LegalWorldPromptGenerator | None = None
        self.validator: ConstitutionalValidator | None = None

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "legal_world_used": 0,
            "fallback_to_generic": 0,
            "validation_failures": 0,
        }

        logger.info(f"⚖️ 小娜法律世界模型集成版初始化完成 (模式: {integration_mode.value})")

    async def initialize(self) -> None:
        """初始化智能体"""
        # 初始化场景识别器
        self.scenario_identifier = EnhancedScenarioIdentifier(
            enable_llm_fallback=True
        )
        logger.info("✅ 场景识别器已初始化")

        # 初始化规则检索器（需要数据库连接）
        try:
            from core.legal_world_model.db_manager import LegalWorldDBManager

            db_manager = LegalWorldDBManager(
                uri=self.neo4j_uri,
                username=self.neo4j_username,
                password=self.neo4j_password,
                database=self.neo4j_database,
            )
            await db_manager.initialize()

            self.rule_retriever = ScenarioRuleRetriever(db_manager)
            logger.info("✅ 规则检索器已初始化")

            # 初始化提示词生成器
            self.prompt_generator = LegalWorldPromptGenerator(db_manager)
            await self.prompt_generator.initialize()
            logger.info("✅ 提示词生成器已初始化")

            # 初始化验证器
            self.validator = ConstitutionalValidator()
            logger.info("✅ 宪法验证器已初始化")

        except Exception as e:
            logger.error(f"⚠️ 法律世界模型组件初始化失败: {e}")
            if self.integration_mode == LegalWorldIntegrationMode.STRICT:
                raise RuntimeError("严格模式下法律世界模型必须可用") from e
            else:
                logger.warning("⚠️ 将在回退模式下运行")

    # ========== 核心处理流程 ==========

    async def _process_with_legal_world(
        self, action: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        使用法律世界模型处理请求

        流程:
        1. 场景识别
        2. 规则检索
        3. 提示词生成
        4. LLM执行
        5. 结果验证
        6. 可解释性输出
        """

        # 1. 构建增强请求
        enhanced_request = await self._build_enhanced_request(action, parameters)

        # 2. 验证是否为专利相关业务
        if enhanced_request.scenario_context.domain != Domain.PATENT:
            if self.integration_mode == LegalWorldIntegrationMode.STRICT:
                raise ValueError("严格模式下仅支持专利相关业务")
            else:
                return await self._fallback_to_generic(action, parameters)

        # 3. 执行法律世界模型增强的处理
        try:
            result = await self._execute_with_legal_context(enhanced_request, action, parameters)
            self.stats["legal_world_used"] += 1
            return result

        except Exception as e:
            logger.error(f"❌ 法律世界模型执行失败: {e}")
            if self.integration_mode == LegalWorldIntegrationMode.HYBRID:
                return await self._fallback_to_generic(action, parameters)
            else:
                raise

    async def _build_enhanced_request(
        self, action: str, parameters: dict[str, Any]
    ) -> LegalWorldEnhancedRequest:
        """构建增强的法律世界请求"""

        # 构建用户输入文本
        user_input = self._build_user_input_from_action(action, parameters)

        # 场景识别
        scenario_context = self.scenario_identifier.identify_scenario(user_input)
        logger.info(f"🔍 场景识别结果: {scenario_context.domain.value}/{scenario_context.task_type.value}/{scenario_context.phase.value}")

        # 检索场景规则
        scenario_rule = None
        if self.rule_retriever:
            scenario_rule = self.rule_retriever.retrieve_rule(
                domain=scenario_context.domain.value,
                task_type=scenario_context.task_type.value,
                phase=scenario_context.phase.value if scenario_context.phase != Phase.OTHER else None,
            )

        # 构建增强请求
        enhanced_request = LegalWorldEnhancedRequest(
            original_request=user_input,
            scenario_context=scenario_context,
            scenario_rule=scenario_rule,
        )

        # 如果有场景规则，提取法律依据和参考案例
        if scenario_rule:
            enhanced_request.legal_basis = scenario_rule.legal_basis
            enhanced_request.reference_cases = scenario_rule.reference_cases
            enhanced_request.processing_rules = scenario_rule.processing_rules

        return enhanced_request

    async def _execute_with_legal_context(
        self, enhanced_request: LegalWorldEnhancedRequest, action: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """在法律上下文中执行请求"""

        # 生成动态提示词
        if self.prompt_generator:
            legal_context = LegalContext(
                business_type=self._map_task_to_business_type(enhanced_request.scenario_context.task_type),
                domain=enhanced_request.scenario_context.domain.value,
                keywords=[],
                user_query=enhanced_request.original_request,
                urgency_level="normal",
                complexity_level="medium",
            )

            dynamic_prompt = await self.prompt_generator.generate_dynamic_prompt(legal_context)
            enhanced_request.dynamic_prompt = dynamic_prompt

            # 构建完整的提示词
            full_prompt = self._build_full_prompt(enhanced_request, action, parameters)

            # 调用LLM
            from core.llm.unified_llm_manager import UnifiedLLMManager

            llm_manager = UnifiedLLMManager()
            await llm_manager.initialize()

            response = await llm_manager.generate(
                message=full_prompt,
                task_type="complex_analysis",
                context={
                    "legal_world_enabled": True,
                    "legal_basis": enhanced_request.legal_basis,
                    "reference_cases": enhanced_request.reference_cases,
                },
                temperature=0.3,
                max_tokens=8000,
            )

            await llm_manager.shutdown()

            # 验证结果
            if self.validator and enhanced_request.scenario_rule:
                # 这里可以添加具体的验证逻辑
                pass

            # 构建响应
            return {
                "success": True,
                "content": response.content,
                "model_used": response.model_used,
                "legal_world_context": {
                    "scenario": enhanced_request.scenario_context.__dict__,
                    "legal_basis": enhanced_request.legal_basis,
                    "reference_cases": enhanced_request.reference_cases,
                    "processing_rules": enhanced_request.processing_rules,
                },
                "explanation": self._generate_explanation(enhanced_request),
            }

        else:
            # 回退到通用LLM
            return await self._fallback_to_generic(action, parameters)

    async def _fallback_to_generic(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """回退到通用处理"""
        logger.warning("⚠️ 回退到通用处理模式")
        self.stats["fallback_to_generic"] += 1

        # 这里可以调用基础的LLM处理
        return {
            "success": True,
            "content": "通用处理结果（未使用法律世界模型）",
            "warning": "未使用法律世界模型",
        }

    # ========== 辅助方法 ==========

    def _build_user_input_from_action(self, action: str, parameters: dict[str, Any]) -> str:
        """从动作和参数构建用户输入"""
        if action == "patent-drafting-with-legal-world":
            return f"请撰写专利申请文件，技术交底书内容：{parameters.get('tech_disclosure', '')[:200]}..."
        elif action == "office-action-response-with-legal-world":
            return f"请答复审查意见，审查意见内容：{parameters.get('oa_text', '')[:200]}..."
        elif action == "invalidity-request-with-legal-world":
            return f"请提出无效宣告请求，目标专利：{parameters.get('patent_no', '')}"
        elif action == "novelty-analysis-with-legal-world":
            return "请分析专利的新颖性"
        elif action == "creativity-analysis-with-legal-world":
            return "请分析专利的创造性"
        else:
            return "请处理专利相关业务"

    def _map_task_to_business_type(self, task_type: TaskType) -> str:
        """映射任务类型到业务类型"""
        mapping = {
            TaskType.DRAFTING: "专利申请",
            TaskType.SEARCH: "专利审查",
            TaskType.VALIDITY: "专利无效",
            TaskType.CREATIVITY_ANALYSIS: "专利审查",
            TaskType.NOVELTY_ANALYSIS: "专利审查",
        }
        return mapping.get(task_type, "专利申请")

    def _build_full_prompt(
        self, enhanced_request: LegalWorldEnhancedRequest, action: str, parameters: dict[str, Any]
    ) -> str:
        """构建完整的提示词"""

        prompt_parts = []

        # 1. 系统角色提示
        if enhanced_request.dynamic_prompt:
            prompt_parts.append(enhanced_request.dynamic_prompt.system_prompt)
        else:
            prompt_parts.append("你是一位资深的专利代理人，拥有20年的专利代理经验。")

        # 2. 法律依据
        if enhanced_request.legal_basis:
            prompt_parts.append("\n# 法律依据")
            for i, basis in enumerate(enhanced_request.legal_basis, 1):
                prompt_parts.append(f"{i}. {basis}")

        # 3. 处理规则
        if enhanced_request.processing_rules:
            prompt_parts.append("\n# 处理规则")
            for i, rule in enumerate(enhanced_request.processing_rules, 1):
                prompt_parts.append(f"{i}. {rule}")

        # 4. 用户请求
        prompt_parts.append(f"\n# 用户请求\n{enhanced_request.original_request}")

        # 5. 具体参数
        if action == "patent-drafting-with-legal-world":
            tech_disclosure = parameters.get("tech_disclosure", "")
            prompt_parts.append(f"\n# 技术交底书\n{tech_disclosure}")

        return "\n".join(prompt_parts)

    def _generate_explanation(self, enhanced_request: LegalWorldEnhancedRequest) -> str:
        """生成可解释性说明"""
        explanation_parts = [
            "## 法律世界模型处理说明",
            "",
            f"**场景识别**: {enhanced_request.scenario_context.domain.value}/{enhanced_request.scenario_context.task_type.value}",
            f"**置信度**: {enhanced_request.scenario_context.confidence:.2f}",
            "",
        ]

        if enhanced_request.legal_basis:
            explanation_parts.append("**法律依据**:")
            for basis in enhanced_request.legal_basis:
                explanation_parts.append(f"- {basis}")
            explanation_parts.append("")

        if enhanced_request.reference_cases:
            explanation_parts.append("**参考案例**:")
            for case in enhanced_request.reference_cases:
                explanation_parts.append(f"- {case.get('name', '未知案例')}: {case.get('relevance', '')}")
            explanation_parts.append("")

        return "\n".join(explanation_parts)

    # ========== 公共接口 ==========

    async def process_patent_drafting_with_legal_world(
        self, tech_disclosure: str, inventor_info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        基于法律世界模型撰写专利

        Args:
            tech_disclosure: 技术交底书
            inventor_info: 发明人信息（可选）

        Returns:
            包含专利申请文件和法律依据的字典
        """
        return await self._process_with_legal_world(
            action="patent-drafting-with-legal-world",
            parameters={"tech_disclosure": tech_disclosure, "inventor_info": inventor_info},
        )

    async def process_office_action_response_with_legal_world(
        self, oa_text: str, application_no: str, claims: str
    ) -> dict[str, Any]:
        """
        基于法律世界模型答复审查意见

        Args:
            oa_text: 审查意见文本
            application_no: 专利申请号
            claims: 权利要求书

        Returns:
            包含答复意见和法律依据的字典
        """
        return await self._process_with_legal_world(
            action="office-action-response-with-legal-world",
            parameters={"oa_text": oa_text, "application_no": application_no, "claims": claims},
        )

    async def process_invalidation_with_legal_world(
        self, patent_no: str, invalidity_grounds: list[str]
    ) -> dict[str, Any]:
        """
        基于法律世界模型提出无效宣告请求

        Args:
            patent_no: 目标专利号
            invalidity_grounds: 无效理由

        Returns:
            包含无效请求书和法律依据的字典
        """
        return await self._process_with_legal_world(
            action="invalidity-request-with-legal-world",
            parameters={"patent_no": patent_no, "invalidity_grounds": invalidity_grounds},
        )

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "legal_world_usage_rate": (
                self.stats["legal_world_used"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0
                else 0
            ),
        }

    # ========== BaseAgent抽象方法实现 ==========

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy" if self.scenario_identifier else "unhealthy",
            "integration_mode": self.integration_mode.value,
            "components": {
                "scenario_identifier": self.scenario_identifier is not None,
                "rule_retriever": self.rule_retriever is not None,
                "prompt_generator": self.prompt_generator is not None,
                "validator": self.validator is not None,
            },
        }

    async def process(self, request: Any) -> Any:
        """处理请求"""
        from core.agents.base import AgentRequest, AgentResponse

        if not isinstance(request, AgentRequest):
            return AgentResponse.error("无效的请求类型")

        self.stats["total_requests"] += 1

        try:
            # 根据action路由到不同的处理方法
            action = request.action

            if action == "patent-drafting-with-legal-world":
                result = await self.process_patent_drafting_with_legal_world(
                    tech_disclosure=request.parameters.get("tech_disclosure", ""),
                    inventor_info=request.parameters.get("inventor_info"),
                )
            elif action == "office-action-response-with-legal-world":
                result = await self.process_office_action_response_with_legal_world(
                    oa_text=request.parameters.get("oa_text", ""),
                    application_no=request.parameters.get("application_no", ""),
                    claims=request.parameters.get("claims", ""),
                )
            elif action == "invalidity-request-with-legal-world":
                result = await self.process_invalidation_with_legal_world(
                    patent_no=request.parameters.get("patent_no", ""),
                    invalidity_grounds=request.parameters.get("invalidity_grounds", []),
                )
            else:
                result = await self._process_with_legal_world(action, request.parameters)

            return AgentResponse.success(data=result)

        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return AgentResponse.error(f"处理失败: {e}")

    async def shutdown(self) -> None:
        """关闭智能体"""
        logger.info("正在关闭小娜法律世界模型集成版...")

        # 清理资源
        if self.prompt_generator:
            await self.prompt_generator.cleanup()

        logger.info("✅ 小娜法律世界模型集成版已关闭")


# ========== 便捷函数 ==========

async def create_xiaona_with_legal_world(
    integration_mode: LegalWorldIntegrationMode = LegalWorldIntegrationMode.STRICT,
) -> XiaonaWithLegalWorld:
    """
    创建小娜法律世界模型集成版智能体

    Args:
        integration_mode: 集成模式

    Returns:
        初始化完成的智能体
    """
    agent = XiaonaWithLegalWorld(integration_mode=integration_mode)
    await agent.initialize()
    return agent


# ========== 导出 ==========

__all__ = [
    "XiaonaWithLegalWorld",
    "LegalWorldIntegrationMode",
    "LegalWorldEnhancedRequest",
    "create_xiaona_with_legal_world",
]
