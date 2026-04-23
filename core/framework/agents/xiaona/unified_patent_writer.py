"""
统一专利撰写代理入口

整合小娜专业代理的所有撰写能力，提供统一接口。

主要功能：
- 专利撰写（DraftingModule）
- 审查答复（ResponseModule）
- 任务编排（OrchestrationModule）
- 通用工具（UtilityModule）

整合方式：
- 统一路由入口
- 模块化调用
- 错误处理和日志
- 进度跟踪
"""

import logging
from datetime import datetime
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)


class UnifiedPatentWriter(BaseXiaonaComponent):
    """
    统一专利撰写代理

    整合小娜专业代理的所有撰写能力，提供统一入口。

    核心能力：
    - 专利撰写模块（7个能力）
    - 审查答复模块（2个能力）
    - 任务编排模块（2个能力）
    - 通用工具模块（2个能力）
    """

    # 系统提示词
    SYSTEM_PROMPT = """你是小娜·撰写者，专利文书撰写专家。

你的核心能力：
1. 权利要求书撰写：独立权利要求和从属权利要求
2. 说明书撰写：完整的技术描述
3. 审查意见答复：针对审查意见的陈述
4. 无效宣告请求书：无效理由和证据组织

撰写原则：
- 法律性：符合专利法及实施细则要求
- 技术性：准确描述技术方案
- 逻辑性：层次清晰、逻辑严谨
- 规范性：符合专利局格式要求

输出格式：
- 权利要求书：独立权利要求 + 从属权利要求
- 说明书：发明名称、技术领域、背景技术、发明内容、附图说明、具体实施方式
- 意见陈述书：意见陈述、修改说明、对比分析
"""

    def __init__(self, config: Optional[dict[str, Any]] = None):

        """
        初始化统一专利撰写代理

        Args:
            config: 配置参数
        """
        # 初始化基类
        super().__init__(agent_id="unified_patent_writer", config=config)

    def _initialize(self) -> str:
        """初始化智能体 - 注册所有能力"""
        # 初始化子模块
        self._init_modules()

        # 注册能力
        self._register_all_capabilities()

        self.logger.info("统一专利撰写代理初始化完成")

    def _init_modules(self) -> str:
        """初始化子模块"""
        from core.framework.agents.xiaona.modules.drafting_module import PatentDraftingModule
        from core.framework.agents.xiaona.modules.orchestration_module import OrchestrationModule
        from core.framework.agents.xiaona.modules.response_module import ResponseModule
        from core.framework.agents.xiaona.modules.utility_module import UtilityModule

        # 初始化LLM客户端
        llm_client = self._get_llm_client()

        # 创建子模块实例
        self.drafting_module = PatentDraftingModule(llm_client=llm_client)
        self.response_module = ResponseModule()
        self.orchestration_module = OrchestrationModule()
        self.utility_module = UtilityModule()

        self.logger.info("子模块初始化完成: drafting, response, orchestration, utility")

    def _get_llm_client(self) -> Any :
        """获取LLM客户端"""
        try:
            # 尝试使用云端适配器
            from core.ai.llm.adapters.cloud_adapter import CloudLLMAdapter

            return CloudLLMAdapter(provider="deepseek", model="chat")
        except Exception as e:
            self.logger.warning(f"云端LLM适配器初始化失败: {e}")
            return None

    def _register_all_capabilities(self) -> str:
        """注册所有核心能力"""
        capabilities = []

        # ========== DraftingModule能力（7个） ==========

        capabilities.extend([
            {
                "name": "analyze_disclosure",
                "description": "分析技术交底书，提取关键信息并评估质量",
                "input_types": ["dict", "file_path"],
                "output_types": ["dict"],
                "estimated_time": 30.0,
            },
            {
                "name": "assess_patentability",
                "description": "评估可专利性，包括新颖性、创造性和实用性分析",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 60.0,
            },
            {
                "name": "draft_specification",
                "description": "撰写说明书，包含技术领域、背景技术、发明内容等",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 120.0,
            },
            {
                "name": "draft_claims",
                "description": "撰写权利要求书，包含独立权利要求和从属权利要求",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 90.0,
            },
            {
                "name": "optimize_protection_scope",
                "description": "优化保护范围，提供权利要求修改建议",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 45.0,
            },
            {
                "name": "review_adequacy",
                "description": "审查充分公开，检查技术方案描述是否完整",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 30.0,
            },
            {
                "name": "detect_common_errors",
                "description": "检测常见错误，包括格式、术语和逻辑问题",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 20.0,
            },
        ])

        # ========== ResponseModule能力（2个） ==========

        capabilities.extend([
            {
                "name": "draft_response",
                "description": "撰写审查意见答复陈述书",
                "input_types": ["dict", "str"],
                "output_types": ["dict"],
                "estimated_time": 150.0,
            },
            {
                "name": "draft_invalidation",
                "description": "撰写无效宣告请求书",
                "input_types": ["dict", "str"],
                "output_types": ["dict"],
                "estimated_time": 180.0,
            },
        ])

        # ========== OrchestrationModule能力（2个） ==========

        capabilities.extend([
            {
                "name": "draft_full_application",
                "description": "完整专利申请流程编排，从交底书到申请文件",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 600.0,
            },
            {
                "name": "orchestrate_response",
                "description": "审查意见答复流程编排，包含检索、分析、撰写",
                "input_types": ["dict"],
                "output_types": ["dict"],
                "estimated_time": 400.0,
            },
        ])

        # ========== UtilityModule能力（2个） ==========

        capabilities.extend([
            {
                "name": "format_document",
                "description": "格式化文档，支持权利要求书、说明书等标准格式",
                "input_types": ["str", "dict"],
                "output_types": ["str"],
                "estimated_time": 10.0,
            },
            {
                "name": "calculate_quality_score",
                "description": "计算文档质量评分，包括完整性、规范性、逻辑性",
                "input_types": ["str"],
                "output_types": ["dict"],
                "estimated_time": 15.0,
            },
        ])

        # 注册能力
        self._register_capabilities(capabilities)

        self.logger.info(f"已注册 {len(capabilities)} 个核心能力")

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            # 验证输入
            if not self.validate_input(context):
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message="输入验证失败",
                    execution_time=0.0,
                )

            # 获取任务类型
            task_type = context.input_data.get("task_type", "")
            if not task_type:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message="缺少task_type参数",
                    execution_time=0.0,
                )

            # 路由到对应模块
            result = await self._route_to_module(task_type, context)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.exception(f"任务执行失败: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    async def _route_to_module(
        self, task_type: str, context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        根据任务类型路由到对应模块

        Args:
            task_type: 任务类型
            context: 执行上下文

        Returns:
            处理结果
        """
        # DraftingModule能力
        drafting_tasks = {
            "analyze_disclosure",
            "assess_patentability",
            "draft_specification",
            "draft_claims",
            "optimize_protection_scope",
            "review_adequacy",
            "detect_common_errors",
        }

        # ResponseModule能力
        response_tasks = {
            "draft_response",
            "draft_invalidation",
        }

        # OrchestrationModule能力
        orchestration_tasks = {
            "draft_full_application",
            "orchestrate_response",
        }

        # UtilityModule能力
        utility_tasks = {
            "format_document",
            "calculate_quality_score",
        }

        if task_type in drafting_tasks:
            return await self._route_to_drafting_module(task_type, context)
        elif task_type in response_tasks:
            return await self._route_to_response_module(task_type, context)
        elif task_type in orchestration_tasks:
            return await self._route_to_orchestration_module(task_type, context)
        elif task_type in utility_tasks:
            return await self._route_to_utility_module(task_type, context)
        else:
            raise ValueError(f"不支持的任务类型: {task_type}")

    async def _route_to_drafting_module(
        self, task_type: str, context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        路由到专利撰写模块

        Args:
            task_type: 任务类型
            context: 执行上下文

        Returns:
            处理结果
        """
        self.logger.info(f"路由到DraftingModule: {task_type}")

        # 获取输入数据
        input_data = context.input_data.get("data", {})

        # 根据任务类型调用对应方法
        if task_type == "analyze_disclosure":
            return await self.drafting_module.analyze_disclosure(input_data)
        elif task_type == "assess_patentability":
            return await self.drafting_module.assess_patentability(input_data)
        elif task_type == "draft_specification":
            return await self.drafting_module.draft_specification(input_data)
        elif task_type == "draft_claims":
            return await self.drafting_module.draft_claims(input_data)
        elif task_type == "optimize_protection_scope":
            return await self.drafting_module.optimize_protection_scope(input_data)
        elif task_type == "review_adequacy":
            return await self.drafting_module.review_adequacy(input_data)
        elif task_type == "detect_common_errors":
            return await self.drafting_module.detect_common_errors(input_data)
        else:
            raise ValueError(f"DraftingModule不支持的任务类型: {task_type}")

    async def _route_to_response_module(
        self, task_type: str, context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        路由到审查答复模块

        Args:
            task_type: 任务类型
            context: 执行上下文

        Returns:
            处理结果
        """
        self.logger.info(f"路由到ResponseModule: {task_type}")

        # 获取输入数据
        user_input = context.input_data.get("user_input", "")
        previous_results = context.input_data.get("previous_results", {})
        model = context.input_data.get("model", "kimi-k2.5")

        # 根据任务类型调用对应方法
        if task_type == "draft_response":
            return await self.response_module.draft_response(user_input, previous_results, model)
        elif task_type == "draft_invalidation":
            return await self.response_module.draft_invalidation(user_input, previous_results, model)
        else:
            raise ValueError(f"ResponseModule不支持的任务类型: {task_type}")

    async def _route_to_orchestration_module(
        self, task_type: str, context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        路由到任务编排模块

        Args:
            task_type: 任务类型
            context: 执行上下文

        Returns:
            处理结果
        """
        self.logger.info(f"路由到OrchestrationModule: {task_type}")

        # 获取输入数据
        input_data = context.input_data.get("data", {})
        progress_callback = context.input_data.get("progress_callback")

        # 根据任务类型调用对应方法
        if task_type == "draft_full_application":
            return await self.orchestration_module.draft_full_application(input_data, progress_callback)
        elif task_type == "orchestrate_response":
            office_action = context.input_data.get("office_action", {})
            patent_data = context.input_data.get("patent_data")
            search_existing_art = context.input_data.get("search_existing_art", True)
            return await self.orchestration_module.orchestrate_response(
                office_action, patent_data, search_existing_art, progress_callback
            )
        else:
            raise ValueError(f"OrchestrationModule不支持的任务类型: {task_type}")

    async def _route_to_utility_module(
        self, task_type: str, context: AgentExecutionContext
    ) -> dict[str, Any]:
        """
        路由到通用工具模块

        Args:
            task_type: 任务类型
            context: 执行上下文

        Returns:
            处理结果
        """
        self.logger.info(f"路由到UtilityModule: {task_type}")

        # 获取输入数据
        input_data = context.input_data.get("data", {})

        # 根据任务类型调用对应方法
        if task_type == "format_document":
            document_type = input_data.get("document_type", "specification")
            content = input_data.get("content", "")
            result = self.utility_module.format_document(document_type, content, **input_data)
            return {"formatted_document": result}
        elif task_type == "calculate_quality_score":
            document_content = input_data.get("document_content", "")
            review_result = input_data.get("review_result")
            metrics = self.utility_module.calculate_quality_score(document_content, review_result)
            return {
                "quality_metrics": {
                    "completeness": metrics.completeness,
                    "standardization": metrics.standardization,
                    "logic": metrics.logic,
                    "overall": metrics.overall,
                }
            }
        else:
            raise ValueError(f"UtilityModule不支持的任务类型: {task_type}")

    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        return self.SYSTEM_PROMPT

    # ========== 便捷方法 ==========

    async def analyze_disclosure(self, disclosure_data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        分析技术交底书（便捷方法）

        Args:
            disclosure_data: 技术交底书数据

        Returns:
            分析报告
        """
        context = AgentExecutionContext(
            session_id="auto",
            task_id="analyze_disclosure",
            input_data={
                "task_type": "analyze_disclosure",
                "data": disclosure_data,
            },
            config={},
            metadata={},
        )
        result = await self.execute(context)
        return result.output_data

    async def draft_full_application(
        self,
        disclosure_data: Optional[dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> dict[str, Any]:
        """
        完整专利申请流程（便捷方法）

        Args:
            disclosure_data: 技术交底书数据
            progress_callback: 进度回调函数

        Returns:
            完整申请文件
        """
        context = AgentExecutionContext(
            session_id="auto",
            task_id="draft_full_application",
            input_data={
                "task_type": "draft_full_application",
                "data": disclosure_data,
                "progress_callback": progress_callback,
            },
            config={},
            metadata={},
        )
        result = await self.execute(context)
        return result.output_data

    async def draft_office_action_response(
        self,
        office_action: Optional[dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> dict[str, Any]:
        """
        审查意见答复流程（便捷方法）

        Args:
            office_action: 审查意见数据
            progress_callback: 进度回调函数

        Returns:
            答复意见
        """
        context = AgentExecutionContext(
            session_id="auto",
            task_id="orchestrate_response",
            input_data={
                "task_type": "orchestrate_response",
                "office_action": office_action,
                "search_existing_art": True,
                "progress_callback": progress_callback,
            },
            config={},
            metadata={},
        )
        result = await self.execute(context)
        return result.output_data


# ========== 工厂函数 ==========

@staticmethod
    def create_unified_patent_writer(config: Optional[dict[str, Any]] = None) -> str:
        """
        创建统一专利撰写代理实例

        Args:
            config: 配置参数

        Returns:
            UnifiedPatentWriter实例
        """
        return UnifiedPatentWriter(config=config)


def get_unified_patent_writer() -> str:
    """
    获取单例统一专利撰写代理实例

    Returns:
        UnifiedPatentWriter实例
    """
    if not hasattr(get_unified_patent_writer, "_instance"):
        get_unified_patent_writer._instance = UnifiedPatentWriter()
    return get_unified_patent_writer._instance
