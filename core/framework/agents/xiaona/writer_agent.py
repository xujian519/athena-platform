"""
小娜·撰写者 - WriterAgent适配器

向后兼容适配器，将旧的WriterAgent接口路由到新的UnifiedPatentWriter。

适配器特性：
- 保留原有类名和基本结构
- 延迟加载UnifiedPatentWriter
- 任务类型自动映射
- 完整错误处理和日志
- 原有方法标记为废弃但可用

迁移说明：
- 旧的writing_type参数映射到新的task_type
- 旧的execute()方法自动路由到UnifiedPatentWriter
- 建议直接使用UnifiedPatentWriter获取新功能
"""

import logging
import warnings
from datetime import datetime
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)

# 任务类型映射表：旧的writing_type → 新的task_type
TASK_TYPE_MAPPING = {
    "claims": "draft_claims",
    "description": "draft_specification",
    "office_action_response": "draft_response",
    "invalidation": "draft_invalidation",
    "full_application": "draft_full_application",
}


class WriterAgent(BaseXiaonaComponent):
    """
    小娜·撰写者（适配器版本）

    向后兼容适配器，将调用路由到UnifiedPatentWriter。

    .. deprecated::
        建议直接使用 UnifiedPatentWriter 获取完整功能。
        此适配器仅用于向后兼容。

    适配的任务类型：
    - claims → draft_claims（权利要求书撰写）
    - description → draft_specification（说明书撰写）
    - office_action_response → draft_response（审查意见答复）
    - invalidation → draft_invalidation（无效宣告请求书）
    - full_application → draft_full_application（完整申请文件）
    """

    # UnifiedPatentWriter实例（延迟加载）
    _unified_writer: Optional["UnifiedPatentWriter"] = None

    def _initialize(self) -> str:
        """初始化撰写者智能体"""
        # 注册能力（保持原有结构）
        self._register_capabilities([

            AgentCapability(
                name="claim_drafting",
                description="权利要求书撰写",
                input_types=["技术交底书", "技术特征"],
                output_types=["权利要求书"],
                estimated_time=30.0,
            ),
            AgentCapability(
                name="description_drafting",
                description="说明书撰写",
                input_types=["技术交底书", "权利要求书"],
                output_types=["说明书"],
                estimated_time=40.0,
            ),
            AgentCapability(
                name="office_action_response",
                description="审查意见答复",
                input_types=["审查意见", "对比文件"],
                output_types=["意见陈述书"],
                estimated_time=60.0,
            ),
            AgentCapability(
                name="invalidation_petition",
                description="无效宣告请求书",
                input_types=["目标专利", "证据"],
                output_types=["无效宣告请求书"],
                estimated_time=90.0,
            ),
        )

        # 初始化LLM（保留原有字段）
        try:
            from core.ai.llm.unified_llm_manager import UnifiedLLMManager
            self.llm_manager = UnifiedLLMManager()
        except Exception as e:
            logger.warning(f"LLM管理器初始化失败: {e}")
            self.llm_manager = None

        self.logger.info(f"撰写者智能体初始化完成（适配器模式）: {self.agent_id}")

    def _get_unified_writer(self) -> "UnifiedPatentWriter":
        """
        获取UnifiedPatentWriter实例（延迟加载）

        Returns:
            UnifiedPatentWriter实例
        """
        if WriterAgent._unified_writer is None:
            from core.framework.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

            WriterAgent._unified_writer = UnifiedPatentWriter()
        return WriterAgent._unified_writer

    def _map_task_type(self, writing_type: str) -> str:
        """
        映射任务类型

        Args:
            writing_type: 旧的writing_type参数

        Returns:
            新的task_type
        """
        mapped = TASK_TYPE_MAPPING.get(writing_type, writing_type)
        if mapped != writing_type:
            self.logger.debug(f"任务类型映射: {writing_type} → {mapped}")
        return mapped

    def _convert_context(
        self,
        old_context: AgentExecutionContext,
        new_task_type: str

    )]) -> str:
        """
        转换上下文格式

        Args:
            old_context: 旧的上下文格式
            new_task_type: 新的任务类型

        Returns:
            转换后的上下文
        """
        # 提取旧格式的数据
        user_input = old_context.input_data.get("user_input", "")
        previous_results = old_context.input_data.get("previous_results", {})
        old_data = old_context.input_data.get("data", {})

        # 构建新格式
        new_input_data: Optional[dict[str, Any] = {]

            "task_type": new_task_type,
        }

        # 根据任务类型添加相应的数据
        if new_task_type in ["draft_claims", "draft_specification", "draft_full_application"]:
            # 专利撰写类任务
            new_input_data["data"] = old_data or {"user_input": user_input}
            if previous_results:
                new_input_data["data"]["previous_results"] = previous_results

        elif new_task_type in ["draft_response", "draft_invalidation"]:
            # 审查答复类任务
            new_input_data["user_input"] = user_input
            new_input_data["previous_results"] = previous_results
            new_input_data["model"] = old_context.config.get("model", "kimi-k2.5")

        return AgentExecutionContext(
            session_id=old_context.session_id,
            task_id=old_context.task_id,
            input_data=new_input_data,
            config=old_context.config,
            metadata=old_context.metadata,
        )

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行撰写任务（适配器方法）

        此方法将调用路由到UnifiedPatentWriter。

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()
        writing_type = context.config.get("writing_type", "description")
        task_type = self._map_task_type(writing_type)

        try:
            self.logger.info(f"适配器路由: {writing_type} → {task_type}")

            unified_writer = self._get_unified_writer()
            new_context = self._convert_context(context, task_type)
            result = await unified_writer.execute(new_context)

            # 添加迁移提示
            if result.output_data:
                result.output_data["_adapter_note"] = (
                    f"通过WriterAgent适配器处理。建议迁移到UnifiedPatentWriter直接调用。"
                    f"原任务类型: {writing_type}, 新任务类型: {task_type}"
                )

            return result

        except Exception as e:
            self.logger.exception(f"适配器执行失败: writing_type={writing_type}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=f"适配器错误: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        return """你是小娜·撰写者，专利文书撰写专家。

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

注意：此适配器将自动路由到UnifiedPatentWriter处理。
"""

    # ========== 向后兼容方法（已废弃） ==========

    def _deprecated_warning(self, method_name: str, replacement: str) -> str:
        """发出废弃警告"""
        warnings.warn(f"{method_name}已废弃，建议使用{replacement}。", DeprecationWarning, stacklevel=3)

    async def _draft_claims(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        撰写权利要求书（废弃方法）

        .. deprecated::
            使用 UnifiedPatentWriter.draft_claims() 代替
        """
        self._deprecated_warning("_draft_claims", "UnifiedPatentWriter.draft_claims")

        unified_writer = self._get_unified_writer()
        return await unified_writer.draft_claims(previous_results or {"user_input": user_input})

    async def _draft_description(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        撰写说明书（废弃方法）

        .. deprecated::
            使用 UnifiedPatentWriter.draft_specification() 代替
        """
        self._deprecated_warning("_draft_description", "UnifiedPatentWriter.draft_specification")

        unified_writer = self._get_unified_writer()
        return await unified_writer.draft_specification(previous_results or {"user_input": user_input})

    async def _draft_response(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        撰写审查意见答复（废弃方法）

        .. deprecated::
            使用 UnifiedPatentWriter.draft_response() 代替
        """
        self._deprecated_warning("_draft_response", "UnifiedPatentWriter.draft_response")

        unified_writer = self._get_unified_writer()
        return await unified_writer.response_module.draft_response(
            user_input,
            previous_results,
            "kimi-k2.5"
        )

    async def _draft_invalidation(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        撰写无效宣告请求书（废弃方法）

        .. deprecated::
            使用 UnifiedPatentWriter.draft_invalidation() 代替
        """
        self._deprecated_warning("_draft_invalidation", "UnifiedPatentWriter.draft_invalidation")

        unified_writer = self._get_unified_writer()
        return await unified_writer.response_module.draft_invalidation(
            user_input,
            previous_results,
            "kimi-k2.5"
        )

    async def _draft_full_application(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        撰写完整申请文件（废弃方法）

        .. deprecated::
            使用 UnifiedPatentWriter.draft_full_application() 代替
        """
        self._deprecated_warning("_draft_full_application", "UnifiedPatentWriter.draft_full_application")

        unified_writer = self._get_unified_writer()
        return await unified_writer.draft_full_application(
            previous_results or {"user_input": user_input}
        )

    # ========== 便捷格式化方法（保留） ==========

    @staticmethod
    def _format_claims(claims: Optional[dict[str, Any])] -> str:
        """格式化权利要求书"""
        text = claims.get("independent_claim", "") + "\n\n"
        for claim in claims.get("dependent_claims", []):
            text += claim + "\n"
        return text

    @staticmethod
    def _format_description(description: Optional[dict[str, Any])] -> str:
        """格式化说明书"""
        return "\n\n".join([]

            description.get("title", ""),
            description.get("technical_field", ""),
            description.get("background_art", ""),
            description.get("summary", ""),
            description.get("brief_description", ""),
            description.get("detailed_description", ""),
        )

    @staticmethod
    def _format_response(response: Optional[dict[str, Any])] -> str:
        """格式化意见陈述书"""
        text = response.get("introduction", "") + "\n\n"
        for resp in response.get("responses", []):
            text += f"审查意见：{resp.get('issue', '')}\n"
            text += f"答复：{resp.get('response', '')}\n\n"
        text += response.get("conclusion", "")
        return text

    @staticmethod
    def _format_petition(petition: Optional[dict[str, Any])] -> str:
        """格式化无效宣告请求书"""
        return str(petition)


# ========== 便捷函数 ==========

def create_writer_agent(config: Optional[dict[str, Any]])] -> str:
    """
    创建WriterAgent实例（便捷函数）

    Args:
        config: 配置参数

    Returns:
        WriterAgent实例
    """
    return WriterAgent(config=config)


def get_writer_agent() -> str:
    """
    获取WriterAgent单例实例（便捷函数）

    Returns:
        WriterAgent实例
    """
    if not hasattr(get_writer_agent, "_instance"):
        get_writer_agent._instance = WriterAgent()
    return get_writer_agent._instance


# ========== 迁移辅助函数 ==========

def migrate_to_unified() -> "UnifiedPatentWriter":
    """
    迁移辅助函数 - 获取UnifiedPatentWriter实例

    使用示例：
        # 旧代码
        from core.framework.agents.xiaona.writer_agent import WriterAgent
        writer = WriterAgent()

        # 迁移后
        from core.framework.agents.xiaona.writer_agent import migrate_to_unified
        writer = migrate_to_unified()

    Returns:
        UnifiedPatentWriter实例
    """
    from core.framework.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
    return UnifiedPatentWriter()


def get_task_type_mapping() -> dict[str, str]:
    """
    获取任务类型映射表（用于迁移参考）

    Returns:
        旧的writing_type到新的task_type的映射
    """
    return TASK_TYPE_MAPPING.copy()
