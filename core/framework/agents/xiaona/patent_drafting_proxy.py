"""
专利撰写智能体 - 适配器版本

向后兼容适配器，将原有接口转发到UnifiedPatentWriter。

主要功能：
- 分析技术交底书
- 评估可专利性
- 撰写说明书
- 撰写权利要求书
- 优化保护范围
- 审查充分公开
- 检测常见错误

架构：
- PatentDraftingProxy（适配器层）→ UnifiedPatentWriter（实现层）→ DraftingModule（模块层）
"""

import logging
from datetime import datetime
from typing import Any, cast, Optional

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)


class PatentDraftingProxy(BaseXiaonaComponent):
    """
    专利撰写智能体 - 向后兼容适配器

    这是一个适配器类，将原有接口转发到新的UnifiedPatentWriter实现。

    核心能力（7个）：
    - analyze_disclosure: 分析技术交底书
    - assess_patentability: 评估可专利性
    - draft_specification: 撰写说明书
    - draft_claims: 撰写权利要求书
    - optimize_protection_scope: 优化保护范围
    - review_adequacy: 审查充分公开
    - detect_common_errors: 检测常见错误
    """

    # 延迟加载的UnifiedPatentWriter实例
    _unified_writer: Any = None

    def __init__(
        self, agent_id: str] = "patent_drafting_proxy", config: Optional[dict[str, Any]]
    ):
        """
        初始化专利撰写智能体适配器

        Args:
            agent_id: 智能体唯一标识
            config: 配置参数
        """
        super().__init__(agent_id, config)

    def _initialize(self) -> str:
        """初始化专利撰写智能体适配器"""
        # 注册能力（向后兼容）
        self._register_capabilities(
            []

                {
                    "name": "analyze_disclosure",
                    "description": "分析技术交底书",
                    "input_types": ["技术交底书"],
                    "output_types": ["交底书分析报告"],
                    "estimated_time": 15.0,
                },
                {
                    "name": "assess_patentability",
                    "description": "评估可专利性",
                    "input_types": ["技术交底书", "现有技术"],
                    "output_types": ["可专利性评估报告"],
                    "estimated_time": 20.0,
                },
                {
                    "name": "draft_specification",
                    "description": "撰写说明书",
                    "input_types": ["技术交底书", "可专利性评估"],
                    "output_types": ["说明书草稿"],
                    "estimated_time": 30.0,
                },
                {
                    "name": "draft_claims",
                    "description": "撰写权利要求书",
                    "input_types": ["技术交底书", "说明书"],
                    "output_types": ["权利要求书草稿"],
                    "estimated_time": 25.0,
                },
                {
                    "name": "optimize_protection_scope",
                    "description": "优化保护范围",
                    "input_types": ["权利要求书", "现有技术"],
                    "output_types": ["优化建议"],
                    "estimated_time": 20.0,
                },
                {
                    "name": "review_adequacy",
                    "description": "审查充分公开",
                    "input_types": ["说明书", "权利要求书"],
                    "output_types": ["充分公开审查报告"],
                    "estimated_time": 15.0,
                },
                {
                    "name": "detect_common_errors",
                    "description": "检测常见错误",
                    "input_types": ["说明书", "权利要求书"],
                    "output_types": ["错误检测报告"],
                    "estimated_time": 10.0,
                },
            
        )

        self.logger.info("PatentDraftingProxy适配器初始化完成")

    def _get_unified_writer(self) -> str:
        """
        获取UnifiedPatentWriter实例（延迟加载）

        Returns:
            UnifiedPatentWriter实例
        """
        if PatentDraftingProxy._unified_writer is None:
            try:
                from core.framework.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

                PatentDraftingProxy._unified_writer = UnifiedPatentWriter(config=self.config)
                self.logger.info("UnifiedPatentWriter延迟加载成功")
            except Exception as e:
                self.logger.error(f"UnifiedPatentWriter加载失败: {e}")
                raise RuntimeError(f"无法加载UnifiedPatentWriter: {e}") from e

        return PatentDraftingProxy._unified_writer

    def _build_adapter_context(self, task_id: str, data: Optional[dict[str, Any])] -> str:
        """
        构建适配器执行上下文（私有辅助方法）

        Args:
            task_id: 任务ID
            data: 输入数据

        Returns:
            执行上下文
        """
        return AgentExecutionContext(
            session_id="adapter",
            task_id=task_id,
            input_data={"task_type": task_id, "data": data},
            config=self.config or {},
            metadata={},
        )

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行智能体任务（转发到UnifiedPatentWriter）

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

            unified_writer = self._get_unified_writer()
            self.logger.info(f"转发任务到UnifiedPatentWriter: {context.task_id}")
            result = await unified_writer.execute(context)

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=result.status,
                output_data=result.output_data,
                error_message=result.error_message,
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        except Exception as e:
            self.logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    # ========== 向后兼容接口 ==========

    async def analyze_disclosure(self, disclosure_data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        分析技术交底书（向后兼容接口）

        Args:
            disclosure_data: 技术交底书数据

        Returns:
            交底书分析报告
        """
        try:
            unified_writer = self._get_unified_writer()
            self.logger.info("analyze_disclosure -> 转发到UnifiedPatentWriter")
            return await unified_writer.analyze_disclosure(disclosure_data)
        except Exception as e:
            self.logger.error(f"analyze_disclosure失败: {e}")
            return {
                "error": str(e),
                "disclosure_id": disclosure_data.get("disclosure_id", "未知"),
            }

    async def assess_patentability(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        评估可专利性（向后兼容接口）

        Args:
            data: 包含技术交底书和现有技术的数据

        Returns:
            可专利性评估报告
        """
        try:
            unified_writer = self._get_unified_writer()
            context = self._build_adapter_context("assess_patentability", data)
            self.logger.info("assess_patentability -> 转发到UnifiedPatentWriter")
            result = await unified_writer.execute(context)
            return result.output_data if result.status == AgentStatus.COMPLETED else {"error": result.error_message}
        except Exception as e:
            self.logger.error(f"assess_patentability失败: {e}")
            return {"error": str(e)}

    async def draft_specification(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        撰写说明书（向后兼容接口）

        Args:
            data: 包含技术交底书和可专利性评估的数据

        Returns:
            说明书草稿
        """
        try:
            unified_writer = self._get_unified_writer()
            context = self._build_adapter_context("draft_specification", data)
            self.logger.info("draft_specification -> 转发到UnifiedPatentWriter")
            result = await unified_writer.execute(context)
            return result.output_data if result.status == AgentStatus.COMPLETED else {"error": result.error_message}
        except Exception as e:
            self.logger.error(f"draft_specification失败: {e}")
            return {"error": str(e)}

    async def draft_claims(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        撰写权利要求书（向后兼容接口）

        Args:
            data: 包含技术交底书和说明书的数据

        Returns:
            权利要求书草稿
        """
        try:
            unified_writer = self._get_unified_writer()
            context = self._build_adapter_context("draft_claims", data)
            self.logger.info("draft_claims -> 转发到UnifiedPatentWriter")
            result = await unified_writer.execute(context)
            return result.output_data if result.status == AgentStatus.COMPLETED else {"error": result.error_message}
        except Exception as e:
            self.logger.error(f"draft_claims失败: {e}")
            return {"error": str(e)}

    async def optimize_protection_scope(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        优化保护范围（向后兼容接口）

        Args:
            data: 包含权利要求书和现有技术的数据

        Returns:
            优化建议
        """
        try:
            unified_writer = self._get_unified_writer()
            context = self._build_adapter_context("optimize_protection_scope", data)
            self.logger.info("optimize_protection_scope -> 转发到UnifiedPatentWriter")
            result = await unified_writer.execute(context)
            return result.output_data if result.status == AgentStatus.COMPLETED else {"error": result.error_message}
        except Exception as e:
            self.logger.error(f"optimize_protection_scope失败: {e}")
            return {"error": str(e)}

    async def review_adequacy(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        审查充分公开（向后兼容接口）

        Args:
            data: 包含说明书和权利要求书的数据

        Returns:
            充分公开审查报告
        """
        try:
            unified_writer = self._get_unified_writer()
            context = self._build_adapter_context("review_adequacy", data)
            self.logger.info("review_adequacy -> 转发到UnifiedPatentWriter")
            result = await unified_writer.execute(context)
            return result.output_data if result.status == AgentStatus.COMPLETED else {"error": result.error_message}
        except Exception as e:
            self.logger.error(f"review_adequacy失败: {e}")
            return {"error": str(e)}

    async def detect_common_errors(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        检测常见错误（向后兼容接口）

        Args:
            data: 包含说明书和权利要求书的数据

        Returns:
            错误检测报告
        """
        try:
            unified_writer = self._get_unified_writer()
            context = self._build_adapter_context("detect_common_errors", data)
            self.logger.info("detect_common_errors -> 转发到UnifiedPatentWriter")
            result = await unified_writer.execute(context)
            return result.output_data if result.status == AgentStatus.COMPLETED else {"error": result.error_message}
        except Exception as e:
            self.logger.error(f"detect_common_errors失败: {e}")
            return {"error": str(e)}

    async def draft_patent_application(self, data: Optional[dict[str, Any])] -> dict[str, Any]:
        """
        完整专利申请撰写流程（向后兼容接口）

        Args:
            data: 技术交底书数据

        Returns:
            完整的专利申请文件
        """
        try:
            unified_writer = self._get_unified_writer()
            self.logger.info("draft_patent_application -> 转发到UnifiedPatentWriter")
            return await unified_writer.draft_full_application(data)
        except Exception as e:
            self.logger.error(f"draft_patent_application失败: {e}")
            return {
                "error": str(e),
                "disclosure_id": data.get("disclosure_id", "未知"),
            }

    def get_system_prompt(self, task_type: Optional[str] = None) -> str:
        """
        获取系统提示词（向后兼容接口）

        Args:
            task_type: 任务类型（已废弃，保留用于兼容）

        Returns:
            系统提示词
        """
        try:
            unified_writer = self._get_unified_writer()
            return unified_writer.get_system_prompt()
        except Exception as e:
            self.logger.warning(f"获取系统提示词失败: {e}，使用默认提示词")
            return """你是一位专业的专利撰写专家，具备深厚的专利法知识和丰富的撰写经验。

请以专业、严谨的态度进行工作，并提供明确的建议。
输出必须是严格的JSON格式，不要添加任何额外的文字说明。
"""


# ========== 工厂函数（向后兼容） ==========

def create_patent_drafting_proxy(
    agent_id: str] = "patent_drafting_proxy", config: Optional[dict[str, Any]]
) -> str:
    """
    创建专利撰写代理实例（向后兼容工厂函数）

    Args:
        agent_id: 智能体唯一标识
        config: 配置参数

    Returns:
        PatentDraftingProxy实例
    """
    return PatentDraftingProxy(agent_id=agent_id, config=config)


def get_patent_drafting_proxy() -> str:
    """
    获取单例专利撰写代理实例（向后兼容工厂函数）

    Returns:
        PatentDraftingProxy实例
    """
    if not hasattr(get_patent_drafting_proxy, "_instance"):
        get_patent_drafting_proxy._instance = PatentDraftingProxy()
    return cast(PatentDraftingProxy, get_patent_drafting_proxy._instance)
