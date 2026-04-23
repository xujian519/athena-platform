from __future__ import annotations
"""
法律研究工作流
Legal Research Workflow

实现法律研究的完整工作流，包括法律问题解析、法规检索、案例检索、法理分析和法律意见生成。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from core.agents.task_tool import TaskTool

logger = logging.getLogger(__name__)


@dataclass
class LegalWorkflowInput:
    """法律研究工作流输入"""

    legal_query: str  # 法律问题/查询
    query_type: str = "case"  # 查询类型: statute/case/interpretation
    case_types: list[str] = None  # 案例类型: infringement/invalidation/administrative
    time_range: dict[str, str] | None = None  # 时间范围
    include_trend_analysis: bool = False  # 是否包含趋势分析
    generate_opinion: bool = True  # 是否生成法律意见


@dataclass
class LegalWorkflowResult:
    """法律研究工作流结果"""

    success: bool  # 是否成功
    task_id: str  # 任务ID
    legal_query: str  # 法律问题
    query_type: str  # 查询类型
    steps_completed: list[str]  # 完成的步骤
    statutes: list[dict[str, Any]] | None = None  # 相关法律条文
    cases: list[dict[str, Any]] | None = None  # 相关案例
    legal_analysis: Optional[dict[str, Any]] = None  # 法理分析
    trend_analysis: Optional[dict[str, Any]] = None  # 趋势分析
    legal_opinion: Optional[str] = None  # 法律意见
    error: Optional[str] = None  # 错误信息
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


class LegalWorkflow:
    """法律研究工作流类

    实现法律研究的完整工作流，包括：
    1. 法律问题解析
    2. 法规检索
    3. 案例检索
    4. 法理分析
    5. 法律意见生成
    """

    def __init__(
        self,
        task_tool: TaskTool | None = None,
        config: Optional[dict[str, Any]] = None,
    ):
        """初始化法律研究工作流

        Args:
            task_tool: TaskTool实例
            config: 配置字典
        """
        self.config = config or {}
        self.task_tool = task_tool or TaskTool(config=self.config)

        # 工作流步骤配置
        self.workflow_steps = [
            "legal_query_parser",
            "statute_lookup",
            "case_law_search",
            "legal_reasoning",
            "opinion_generator",
        ]

        logger.info("法律研究工作流初始化完成")

    def execute(self, workflow_input: LegalWorkflowInput) -> LegalWorkflowResult:
        """执行法律研究工作流

        Args:
            workflow_input: 工作流输入

        Returns:
            工作流结果
        """
        logger.info(f"开始执行法律研究工作流: {workflow_input.legal_query}")

        # 初始化结果
        steps_completed = []
        statutes = []
        cases = []
        legal_analysis = {}
        trend_analysis = {}
        legal_opinion = None
        task_id = ""
        error = None

        try:
            # 步骤1: 法律问题解析
            logger.info("步骤1: 法律问题解析...")
            parsed_query = self._step_legal_query_parser(workflow_input.legal_query)
            steps_completed.append("legal_query_parser")

            # 步骤2: 法规检索
            logger.info("步骤2: 法规检索...")
            statutes = self._step_statute_lookup(parsed_query, workflow_input.query_type)
            steps_completed.append("statute_lookup")

            # 步骤3: 案例检索
            logger.info("步骤3: 案例检索...")
            cases = self._step_case_law_search(
                parsed_query,
                workflow_input.case_types,
                workflow_input.time_range,
            )
            steps_completed.append("case_law_search")

            # 步骤4: 法理分析
            logger.info("步骤4: 法理分析...")
            legal_analysis = self._step_legal_reasoning(
                statutes,
                cases,
            )
            steps_completed.append("legal_reasoning")

            # 步骤5: 法律意见生成
            logger.info("步骤5: 法律意见生成...")
            opinion_result = self._step_opinion_generator(
                parsed_query,
                legal_analysis,
            )
            steps_completed.append("opinion_generator")
            legal_opinion = opinion_result.get("content")

            # 趋势分析 (可选)
            if workflow_input.include_trend_analysis:
                logger.info("执行趋势分析...")
                trend_analysis = self._perform_trend_analysis(cases)
            else:
                trend_analysis = None

            # 生成任务ID
            task_id = f"legal-{len(steps_completed)}-{hash(workflow_input.legal_query) % 10000:04d}"

            logger.info(f"法律研究工作流完成: 找到{len(statutes)}条法规, {len(cases)}个案例")

            # 返回成功结果
            return LegalWorkflowResult(
                success=True,
                task_id=task_id,
                legal_query=workflow_input.legal_query,
                query_type=workflow_input.query_type,
                steps_completed=steps_completed,
                statutes=statutes,
                cases=cases,
                legal_analysis=legal_analysis,
                trend_analysis=trend_analysis,
                legal_opinion=legal_opinion,
                error=None,
                metadata={
                    "total_steps": len(steps_completed),
                    "execution_time": "N/A",  # TODO: 添加执行时间
                },
            )

        except Exception as e:
            logger.error(f"法律研究工作流执行失败: {e}", exc_info=True)
            return LegalWorkflowResult(
                success=False,
                task_id=task_id,
                legal_query=workflow_input.legal_query,
                query_type=workflow_input.query_type,
                steps_completed=steps_completed,
                statutes=None,
                cases=None,
                legal_analysis=None,
                trend_analysis=None,
                legal_opinion=None,
                error=str(e),
                metadata={},
            )

    def _step_legal_query_parser(
        self,
        legal_query: str,
    ) -> dict[str, Any]:
        """步骤1: 法律问题解析

        Args:
            legal_query: 法律问题

        Returns:
            解析后的查询
        """
        logger.info(f"解析法律问题: {legal_query}")

        # 使用TaskTool解析法律问题
        result = self.task_tool.execute(
            prompt=f"解析法律问题: {legal_query}",
            tools=["legal-query-parser"],
            agent_type="legal",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"法律问题解析失败: {result}")

        # 返回解析后的查询
        parsed_query = {
            "original_query": legal_query,
            "query_type": "case",  # 占位符
            "key_elements": [
                "关键要素1",  # 占位符
                "关键要素2",  # 占位符
            ],
            "legal_domain": "专利法",  # 占位符
            "source": result.get("source", "unknown"),
        }

        return parsed_query

    def _step_statute_lookup(
        self,
        parsed_query: dict[str, Any],
        query_type: str,
    ) -> list[dict[str, Any]]:
        """步骤2: 法规检索

        Args:
            parsed_query: 解析后的查询
            query_type: 查询类型

        Returns:
            相关法律条文列表
        """
        logger.info(f"检索法律条文 (类型: {query_type})...")

        # 使用TaskTool检索法律条文
        result = self.task_tool.execute(
            prompt=f"检索法律条文: {parsed_query['original_query']}",
            tools=["statute-lookup"],
            agent_type="legal",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"法规检索失败: {result}")

        # 返回法律条文 (TODO: 从实际检索结果中提取)
        statutes = [
            {
                "statute_id": "专利法第25条",
                "title": "专利权的保护范围",
                "content": "发明和实用新型专利权被授予后，除本法另有规定的以外，任何单位或者个人未经专利权人许可，都不得实施其专利...",
                "source": result.get("source", "unknown"),
            },
        ]

        return statutes

    def _step_case_law_search(
        self,
        parsed_query: dict[str, Any],
        case_types: Optional[list[str]],
        time_range: dict[str, str] | None,
    ) -> list[dict[str, Any]]:
        """步骤3: 案例法检索

        Args:
            parsed_query: 解析后的查询
            case_types: 案例类型
            time_range: 时间范围

        Returns:
            相关案例列表
        """
        logger.info("检索案例法...")

        # 使用TaskTool检索案例
        result = self.task_tool.execute(
            prompt=f"检索相关案例: {parsed_query['original_query']}",
            tools=["case-law-search"],
            agent_type="legal",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"案例法检索失败: {result}")

        # 返回案例 (TODO: 从实际检索结果中提取)
        cases = [
            {
                "case_id": "案例001",
                "title": "专利侵权纠纷案",
                "court": "北京市高级人民法院",
                "date": "2023-05-15",
                "case_type": case_types[0] if case_types else "infringement",
                "summary": "本案涉及专利侵权纠纷...",
                "source": result.get("source", "unknown"),
            },
        ]

        return cases

    def _step_legal_reasoning(
        self,
        statutes: list[dict[str, Any]],
        cases: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """步骤4: 法理分析

        Args:
            statutes: 法律条文列表
            cases: 案例列表

        Returns:
            法理分析结果
        """
        logger.info("执行法理分析...")

        # 使用TaskTool执行法理分析
        result = self.task_tool.execute(
            prompt="分析法律条文和案例的法理",
            tools=["legal-reasoning"],
            agent_type="legal",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"法理分析失败: {result}")

        # 返回法理分析
        legal_analysis = {
            "statute_application": "法律条文应用分析",
            "case_consistency": "案例一致性分析",
            "legal_principles": [
                "法律原则1",  # 占位符
                "法律原则2",  # 占位符
            ],
            "conclusion": "法理分析结论",
            "source": result.get("source", "unknown"),
        }

        return legal_analysis

    def _step_opinion_generator(
        self,
        parsed_query: dict[str, Any],
        legal_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """步骤5: 法律意见生成

        Args:
            parsed_query: 解析后的查询
            legal_analysis: 法理分析

        Returns:
            法律意见生成结果
        """
        logger.info("生成法律意见...")

        # 使用TaskTool生成法律意见
        result = self.task_tool.execute(
            prompt="生成法律意见书",
            tools=["opinion-generator"],
            agent_type="legal",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"法律意见生成失败: {result}")

        # 返回法律意见
        return {
            "content": f"""# 法律意见书

## 一、法律问题
{parsed_query["original_query"]}

## 二、相关法律条文
{legal_analysis.get("statute_application", "N/A")}

## 三、案例分析
{legal_analysis.get("case_consistency", "N/A")}

## 四、法律意见
根据相关法律条文和案例分析，提出以下法律意见：

1. [意见要点1]
2. [意见要点2]
3. [意见要点3]

## 五、建议
1. [建议1]
2. [建议2]

---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
""",
            "format": "markdown",
            "source": result.get("source", "unknown"),
        }

    def _perform_trend_analysis(
        self,
        cases: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """执行趋势分析

        Args:
            cases: 案例列表

        Returns:
            趋势分析结果
        """
        logger.info("执行趋势分析...")

        # 使用TaskTool执行趋势分析
        result = self.task_tool.execute(
            prompt="分析法律趋势",
            tools=["trend-analyzer"],
            agent_type="legal",
        )

        # 检查结果
        if not result.get("success", True):
            logger.warning("趋势分析失败")
            return {}

        # 返回趋势分析
        return {
            "trend_overview": "法律趋势概述",
            "key_changes": [
                "关键变化1",
                "关键变化2",
            ],
            "future_outlook": "未来展望",
            "source": result.get("source", "unknown"),
        }

    def get_workflow_config(self) -> dict[str, Any]:
        """获取工作流配置

        Returns:
            工作流配置字典
        """
        return {
            "name": "法律研究工作流",
            "description": "深入研究专利法律法规和案例",
            "version": "1.0.0",
            "steps": self.workflow_steps,
            "config": self.config,
        }

    def get_supported_query_types(self) -> list[str]:
        """获取支持的查询类型

        Returns:
            支持的查询类型列表
        """
        return ["statute", "case", "interpretation"]

    def get_supported_case_types(self) -> list[str]:
        """获取支持的案例类型

        Returns:
            支持的案例类型列表
        """
        return ["infringement", "invalidation", "administrative"]


# ========== 辅助函数 ==========

from datetime import datetime
