from __future__ import annotations
"""
专利分析工作流
Patent Analysis Workflow

实现专利分析的完整工作流，包括专利检索、技术方案分析、创新点识别、对比分析和报告生成。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from core.agents.task_tool import TaskTool
from core.agents.task_tool.tool_filter import ToolFilter

logger = logging.getLogger(__name__)


@dataclass
class AnalysisWorkflowInput:
    """专利分析工作流输入"""

    patent_number: str  # 专利号
    analysis_type: str = "comprehensive"  # 分析类型: comprehensive/technical/innovation/comparative
    include_comparison: bool = True  # 是否包含对比分析
    generate_report: bool = True  # 是否生成报告
    report_format: str = "markdown"  # 报告格式: markdown/json/pdf
    export_path: str | None = None  # 导出路径


@dataclass
class AnalysisWorkflowResult:
    """专利分析工作流结果"""

    success: bool  # 是否成功
    task_id: str  # 任务ID
    patent_number: str  # 专利号
    analysis_type: str  # 分析类型
    steps_completed: list[str]  # 完成的步骤
    analysis_result: dict[str, Any] | None = None  # 分析结果
    comparison_result: dict[str, Any] | None = None  # 对比结果
    report_content: str | None = None  # 报告内容
    report_path: str | None = None  # 报告路径
    error: str | None = None  # 错误信息
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


class AnalysisWorkflow:
    """专利分析工作流类

    实现专利分析的完整工作流，包括：
    1. 专利检索
    2. 技术方案分析
    3. 创新点识别
    4. 对比分析
    5. 报告生成
    """

    def __init__(
        self,
        task_tool: TaskTool | None = None,
        tool_filter: ToolFilter | None = None,
        config: dict[str, Any] | None = None,
    ):
        """初始化专利分析工作流

        Args:
            task_tool: TaskTool实例
            tool_filter: ToolFilter实例
            config: 配置字典
        """
        self.config = config or {}
        self.task_tool = task_tool or TaskTool(config=self.config)
        self.tool_filter = tool_filter or ToolFilter()

        # 工作流步骤配置
        self.workflow_steps = [
            "patent_search",
            "technical_analysis",
            "innovation_identification",
            "comparison_analysis",
            "report_generation",
        ]

        logger.info("专利分析工作流初始化完成")

    def execute(self, workflow_input: AnalysisWorkflowInput) -> AnalysisWorkflowResult:
        """执行专利分析工作流

        Args:
            workflow_input: 工作流输入

        Returns:
            工作流结果
        """
        logger.info(f"开始执行专利分析工作流: {workflow_input.patent_number}")

        # 初始化结果
        steps_completed = []
        analysis_result = {}
        comparison_result = {}
        report_content = None
        report_path = None
        task_id = ""
        error = None

        try:
            # 步骤1: 专利检索
            logger.info("步骤1: 专利检索...")
            patent_data = self._step_patent_search(workflow_input.patent_number)
            steps_completed.append("patent_search")
            analysis_result["patent_data"] = patent_data

            # 步骤2: 技术方案分析
            logger.info("步骤2: 技术方案分析...")
            technical_analysis = self._step_technical_analysis(patent_data)
            steps_completed.append("technical_analysis")
            analysis_result["technical_analysis"] = technical_analysis

            # 步骤3: 创新点识别
            logger.info("步骤3: 创新点识别...")
            innovation_analysis = self._step_innovation_identification(
                patent_data,
                technical_analysis,
            )
            steps_completed.append("innovation_identification")
            analysis_result["innovation_analysis"] = innovation_analysis

            # 步骤4: 对比分析 (可选)
            if workflow_input.include_comparison:
                logger.info("步骤4: 对比分析...")
                comparison_analysis = self._step_comparison_analysis(
                    patent_data,
                    technical_analysis,
                )
                steps_completed.append("comparison_analysis")
                comparison_result = comparison_analysis

            # 步骤5: 报告生成 (可选)
            if workflow_input.generate_report:
                logger.info("步骤5: 报告生成...")
                report_result = self._step_report_generation(
                    patent_data,
                    analysis_result,
                    comparison_result,
                    workflow_input.report_format,
                )
                steps_completed.append("report_generation")
                report_content = report_result.get("content")
                report_path = report_result.get("path")

            # 生成任务ID
            task_id = f"analysis-{workflow_input.patent_number}-{len(steps_completed)}"

            logger.info(f"专利分析工作流完成: {workflow_input.patent_number}")

            # 返回成功结果
            return AnalysisWorkflowResult(
                success=True,
                task_id=task_id,
                patent_number=workflow_input.patent_number,
                analysis_type=workflow_input.analysis_type,
                steps_completed=steps_completed,
                analysis_result=analysis_result,
                comparison_result=comparison_result if workflow_input.include_comparison else None,
                report_content=report_content,
                report_path=report_path,
                error=None,
                metadata={
                    "total_steps": len(steps_completed),
                    "execution_time": "N/A",  # TODO: 添加执行时间
                },
            )

        except Exception as e:
            logger.error(f"专利分析工作流执行失败: {e}", exc_info=True)
            return AnalysisWorkflowResult(
                success=False,
                task_id=task_id,
                patent_number=workflow_input.patent_number,
                analysis_type=workflow_input.analysis_type,
                steps_completed=steps_completed,
                analysis_result=analysis_result if analysis_result else None,
                comparison_result=None,
                report_content=None,
                report_path=None,
                error=str(e),
                metadata={},
            )

    def _step_patent_search(self, patent_number: str) -> dict[str, Any]:
        """步骤1: 专利检索

        Args:
            patent_number: 专利号

        Returns:
            专利数据字典
        """
        logger.info(f"检索专利: {patent_number}")

        # 使用TaskTool执行专利检索
        result = self.task_tool.execute(
            prompt=f"检索专利: {patent_number}",
            tools=["patent-search"],
            agent_type="analysis",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"专利检索失败: {result}")

        # 返回专利数据 (TODO: 从实际检索结果中提取)
        patent_data = {
            "patent_number": patent_number,
            "title": f"专利 {patent_number} 的标题",  # 占位符
            "abstract": f"专利 {patent_number} 的摘要",  # 占位符
            "claims": f"专利 {patent_number} 的权利要求",  # 占位符
            "source": result.get("source", "unknown"),
        }

        return patent_data

    def _step_technical_analysis(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """步骤2: 技术方案分析

        Args:
            patent_data: 专利数据

        Returns:
            技术分析结果
        """
        logger.info("分析技术方案...")

        # 使用TaskTool执行技术分析
        result = self.task_tool.execute(
            prompt=f"分析专利 {patent_data['patent_number']} 的技术方案",
            tools=["patent-analysis"],
            agent_type="analysis",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"技术方案分析失败: {result}")

        # 返回技术分析结果
        technical_analysis = {
            "technical_field": "技术领域",  # 占位符
            "technical_problem": "技术问题",  # 占位符
            "technical_solution": "技术方案",  # 占位符
            "beneficial_effects": "有益效果",  # 占位符
            "source": result.get("source", "unknown"),
        }

        return technical_analysis

    def _step_innovation_identification(
        self,
        patent_data: dict[str, Any],
        technical_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """步骤3: 创新点识别

        Args:
            patent_data: 专利数据
            technical_analysis: 技术分析结果

        Returns:
            创新点分析结果
        """
        logger.info("识别创新点...")

        # 使用TaskTool执行创新点识别
        result = self.task_tool.execute(
            prompt=f"识别专利 {patent_data['patent_number']} 的创新点",
            tools=["knowledge-graph-query", "embedding-search"],
            agent_type="analysis",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"创新点识别失败: {result}")

        # 返回创新点分析结果
        innovation_analysis = {
            "innovation_points": [
                "创新点1",  # 占位符
                "创新点2",  # 占位符
            ],
            "innovation_score": 8.5,  # 占位符
            "creativity_level": "显著改进",  # 占位符
            "source": result.get("source", "unknown"),
        }

        return innovation_analysis

    def _step_comparison_analysis(
        self,
        patent_data: dict[str, Any],
        technical_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """步骤4: 对比分析

        Args:
            patent_data: 专利数据
            technical_analysis: 技术分析结果

        Returns:
            对比分析结果
        """
        logger.info("执行对比分析...")

        # 使用TaskTool执行对比分析
        result = self.task_tool.execute(
            prompt=f"分析专利 {patent_data['patent_number']} 与现有技术的对比",
            tools=["patent-compare"],
            agent_type="analysis",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"对比分析失败: {result}")

        # 返回对比分析结果
        comparison_analysis = {
            "similar_patents": [
                {"patent_number": "CN123456", "similarity": 0.85},  # 占位符
                {"patent_number": "CN789012", "similarity": 0.72},  # 占位符
            ],
            "differences": [
                "差异点1",  # 占位符
                "差异点2",  # 占位符
            ],
            "novelty_assessment": "具有新颖性",  # 占位符
            "source": result.get("source", "unknown"),
        }

        return comparison_analysis

    def _step_report_generation(
        self,
        patent_data: dict[str, Any],
        analysis_result: dict[str, Any],
        comparison_result: dict[str, Any] | None,
        report_format: str = "markdown",
    ) -> dict[str, Any]:
        """步骤5: 报告生成

        Args:
            patent_data: 专利数据
            analysis_result: 分析结果
            comparison_result: 对比结果
            report_format: 报告格式

        Returns:
            报告生成结果
        """
        logger.info(f"生成报告 (格式: {report_format})...")

        # 使用TaskTool生成报告
        result = self.task_tool.execute(
            prompt=f"生成专利 {patent_data['patent_number']} 的分析报告",
            tools=["report-generator"],
            agent_type="analysis",
        )

        # 检查结果
        if not result.get("success", True):
            raise Exception(f"报告生成失败: {result}")

        # 根据报告格式生成报告内容
        if report_format == "markdown":
            report_content = self._generate_markdown_report(
                patent_data,
                analysis_result,
                comparison_result,
            )
        elif report_format == "json":
            report_content = self._generate_json_report(
                patent_data,
                analysis_result,
                comparison_result,
            )
        elif report_format == "pdf":
            report_content = self._generate_pdf_report(
                patent_data,
                analysis_result,
                comparison_result,
            )
        else:
            raise ValueError(f"不支持的报告格式: {report_format}")

        # 返回报告生成结果
        return {
            "content": report_content,
            "path": f"/path/to/report_{patent_data['patent_number']}.{report_format}",  # 占位符
            "format": report_format,
            "source": result.get("source", "unknown"),
        }

    def _generate_markdown_report(
        self,
        patent_data: dict[str, Any],
        analysis_result: dict[str, Any],
        comparison_result: dict[str, Any] | None,
    ) -> str:
        """生成Markdown格式报告"""

        lines = [
            "# 专利分析报告",
            "",
            f"**专利号**: {patent_data['patent_number']}",
            f"**标题**: {patent_data.get('title', 'N/A')}",
            "",
            "## 1. 专利基本信息",
            "",
            "### 摘要",
            f"{patent_data.get('abstract', 'N/A')}",
            "",
            "### 权利要求",
            f"{patent_data.get('claims', 'N/A')}",
            "",
            "## 2. 技术方案分析",
            "",
            "### 技术领域",
            f"{analysis_result.get('technical_analysis', {}).get('technical_field', 'N/A')}",
            "",
            "### 技术问题",
            f"{analysis_result.get('technical_analysis', {}).get('technical_problem', 'N/A')}",
            "",
            "### 技术方案",
            f"{analysis_result.get('technical_analysis', {}).get('technical_solution', 'N/A')}",
            "",
            "### 有益效果",
            f"{analysis_result.get('technical_analysis', {}).get('beneficial_effects', 'N/A')}",
            "",
        ]

        # 添加创新点分析
        innovation_analysis = analysis_result.get("innovation_analysis", {})
        if innovation_analysis:
            lines.extend(
                [
                    "## 3. 创新点识别",
                    "",
                    "### 创新点列表",
                    "",
                ]
            )
            for i, point in enumerate(innovation_analysis.get("innovation_points", []), 1):
                lines.append(f"{i}. {point}")
            lines.extend(
                [
                    "",
                    "### 创新度评分",
                    f"{innovation_analysis.get('innovation_score', 'N/A')} / 10",
                    "",
                    "### 创造性水平",
                    f"{innovation_analysis.get('creativity_level', 'N/A')}",
                    "",
                ]
            )

        # 添加对比分析
        if comparison_result:
            lines.extend(
                [
                    "## 4. 对比分析",
                    "",
                    "### 相似专利",
                    "",
                ]
            )
            for similar in comparison_result.get("similar_patents", []):
                lines.append(
                    f"- **{similar['patent_number']}**: 相似度 {similar['similarity']:.2f}"
                )
            lines.extend(
                [
                    "",
                    "### 差异点",
                    "",
                ]
            )
            for diff in comparison_result.get("differences", []):
                lines.append(f"- {diff}")
            lines.extend(
                [
                    "",
                    "### 新颖性评估",
                    f"{comparison_result.get('novelty_assessment', 'N/A')}",
                    "",
                ]
            )

        # 添加结论
        lines.extend(
            [
                "## 5. 结论和建议",
                "",
                "### 总体评估",
                "该专利具有[此处填写总体评估]。",
                "",
                "### 建议",
                "",
                "1. [建议1]",
                "2. [建议2]",
                "3. [建议3]",
                "",
                "---",
                "",
                f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(lines)

    def _generate_json_report(
        self,
        patent_data: dict[str, Any],
        analysis_result: dict[str, Any],
        comparison_result: dict[str, Any] | None,
    ) -> str:
        """生成JSON格式报告"""

        import json

        report = {
            "patent_number": patent_data["patent_number"],
            "title": patent_data.get("title"),
            "abstract": patent_data.get("abstract"),
            "claims": patent_data.get("claims"),
            "technical_analysis": analysis_result.get("technical_analysis"),
            "innovation_analysis": analysis_result.get("innovation_analysis"),
            "comparison_analysis": comparison_result,
            "generated_at": datetime.now().isoformat(),
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    def _generate_pdf_report(
        self,
        patent_data: dict[str, Any],
        analysis_result: dict[str, Any],
        comparison_result: dict[str, Any] | None,
    ) -> str:
        """生成PDF格式报告

        注意: 实际PDF生成需要使用额外的库(如reportlab)
        这里只返回占位符字符串
        """

        # 先生成Markdown报告
        markdown_content = self._generate_markdown_report(
            patent_data,
            analysis_result,
            comparison_result,
        )

        # TODO: 使用reportlab或类似库将Markdown转换为PDF
        # 这里返回占位符
        return f"[PDF报告占位符: {len(markdown_content)}字符的Markdown内容需要转换为PDF]"

    def get_workflow_config(self) -> dict[str, Any]:
        """获取工作流配置

        Returns:
            工作流配置字典
        """
        return {
            "name": "专利分析工作流",
            "description": "深度分析专利技术方案和创新点",
            "version": "1.0.0",
            "steps": self.workflow_steps,
            "config": self.config,
        }

    def get_supported_analysis_types(self) -> list[str]:
        """获取支持的分析类型

        Returns:
            支持的分析类型列表
        """
        return [
            "comprehensive",  # 综合分析
            "technical",  # 技术分析
            "innovation",  # 创新点分析
            "comparative",  # 对比分析
        ]

    def get_supported_report_formats(self) -> list[str]:
        """获取支持的报告格式

        Returns:
            支持的报告格式列表
        """
        return ["markdown", "json", "pdf"]


# ========== 辅助函数 ==========

from datetime import datetime
