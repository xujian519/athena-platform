#!/usr/bin/env python3
"""
专利分析工作流测试
Patent Analysis Workflow Tests

测试专利分析工作流的各个步骤和整体执行。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

from unittest.mock import Mock

import pytest

# 导入工作流
from core.patents.workflows.analysis_workflow import (
    AnalysisWorkflow,
    AnalysisWorkflowInput,
)


class TestAnalysisWorkflow:
    """专利分析工作流测试类"""

    @pytest.fixture
    def workflow(self):
        """创建工作流实例"""
        # Mock TaskTool和ToolFilter
        mock_task_tool = Mock()
        mock_task_tool.execute.return_value = {
            "success": True,
            "task_id": "test-task-123",
            "status": "completed",
            "agent_id": "analysis-agent-123",
            "model": "task",
        }

        mock_tool_filter = Mock()

        return AnalysisWorkflow(
            task_tool=mock_task_tool,
            tool_filter=mock_tool_filter,
        )

    def test_initialization(self, workflow):
        """测试工作流初始化"""
        assert workflow is not None
        assert workflow.task_tool is not None
        assert workflow.tool_filter is not None
        assert len(workflow.workflow_steps) == 5

    def test_get_workflow_config(self, workflow):
        """测试获取工作流配置"""
        config = workflow.get_workflow_config()
        assert config["name"] == "专利分析工作流"
        assert "steps" in config
        assert "config" in config

    def test_get_supported_analysis_types(self, workflow):
        """测试获取支持的分析类型"""
        types = workflow.get_supported_analysis_types()
        assert "comprehensive" in types
        assert "technical" in types
        assert "innovation" in types
        assert "comparative" in types
        assert len(types) == 4

    def test_get_supported_report_formats(self, workflow):
        """测试获取支持的报告格式"""
        formats = workflow.get_supported_report_formats()
        assert "markdown" in formats
        assert "json" in formats
        assert "pdf" in formats
        assert len(formats) == 3

    @pytest.mark.unit
    def test_step_patent_search(self, workflow):
        """测试步骤1: 专利检索"""
        patent_data = workflow._step_patent_search("CN202310123456.7")
        assert patent_data is not None
        assert "patent_number" in patent_data
        assert patent_data["patent_number"] == "CN202310123456.7"

    @pytest.mark.unit
    def test_step_technical_analysis(self, workflow):
        """测试步骤2: 技术方案分析"""
        patent_data = {
            "patent_number": "CN202310123456.7",
            "title": "测试专利",
            "abstract": "测试摘要",
            "claims": "测试权利要求",
        }

        result = workflow._step_technical_analysis(patent_data)
        assert result is not None
        assert "technical_field" in result

    @pytest.mark.unit
    def test_step_innovation_identification(self, workflow):
        """测试步骤3: 创新点识别"""
        patent_data = {
            "patent_number": "CN202310123456.7",
        }
        technical_analysis = {
            "technical_field": "测试领域",
        }

        result = workflow._step_innovation_identification(patent_data, technical_analysis)
        assert result is not None
        assert "innovation_points" in result
        assert "innovation_score" in result

    @pytest.mark.unit
    def test_step_comparison_analysis(self, workflow):
        """测试步骤4: 对比分析"""
        patent_data = {
            "patent_number": "CN202310123456.7",
        }
        technical_analysis = {
            "technical_field": "测试领域",
        }

        result = workflow._step_comparison_analysis(patent_data, technical_analysis)
        assert result is not None
        assert "similar_patents" in result
        assert "differences" in result

    @pytest.mark.unit
    def test_step_report_generation_markdown(self, workflow):
        """测试步骤5: 报告生成 - Markdown格式"""
        patent_data = {
            "patent_number": "CN202310123456.7",
            "title": "测试专利",
        }
        analysis_result = {
            "technical_analysis": {
                "technical_field": "测试领域",
            },
            "innovation_analysis": {
                "innovation_points": ["创新点1", "创新点2"],
                "innovation_score": 8.5,
                "creativity_level": "显著改进",
            },
        }
        comparison_result = {
            "similar_patents": [
                {"patent_number": "CN123456", "similarity": 0.85},
            ],
            "differences": ["差异点1"],
        }

        result = workflow._step_report_generation(
            patent_data,
            analysis_result,
            comparison_result,
            "markdown",
        )
        assert result is not None
        assert "content" in result
        assert "# 专利分析报告" in result["content"]

    @pytest.mark.unit
    def test_step_report_generation_json(self, workflow):
        """测试步骤5: 报告生成 - JSON格式"""
        patent_data = {
            "patent_number": "CN202310123456.7",
            "title": "测试专利",
        }
        analysis_result = {
            "technical_analysis": {
                "technical_field": "测试领域",
            },
        }

        result = workflow._step_report_generation(
            patent_data,
            analysis_result,
            None,
            "json",
        )
        assert result is not None
        assert "content" in result
        # 验证JSON格式
        import json

        parsed = json.loads(result["content"])
        assert parsed["patent_number"] == "CN202310123456.7"

    @pytest.mark.unit
    def test_step_report_generation_pdf(self, workflow):
        """测试步骤5: 报告生成 - PDF格式"""
        patent_data = {
            "patent_number": "CN202310123456.7",
            "title": "测试专利",
        }
        analysis_result = {
            "technical_analysis": {
                "technical_field": "测试领域",
            },
        }

        result = workflow._step_report_generation(
            patent_data,
            analysis_result,
            None,
            "pdf",
        )
        assert result is not None
        assert "content" in result
        assert "PDF报告占位符" in result["content"]

    @pytest.mark.integration
    def test_execute_comprehensive_analysis(self, workflow):
        """测试执行综合分析工作流"""
        workflow_input = AnalysisWorkflowInput(
            patent_number="CN202310123456.7",
            analysis_type="comprehensive",
            include_comparison=True,
            generate_report=True,
            report_format="markdown",
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is True
        assert result.task_id is not None
        assert result.patent_number == "CN202310123456.7"
        assert len(result.steps_completed) == 5  # 所有步骤都完成
        assert result.analysis_result is not None
        assert result.comparison_result is not None
        assert result.report_content is not None

    @pytest.mark.integration
    def test_execute_technical_analysis_only(self, workflow):
        """测试执行仅技术分析"""
        workflow_input = AnalysisWorkflowInput(
            patent_number="CN202310123456.7",
            analysis_type="technical",
            include_comparison=False,
            generate_report=False,
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is True
        assert len(result.steps_completed) == 3  # 只执行前3个步骤
        assert result.comparison_result is None  # 不包含对比分析
        assert result.report_content is None  # 不生成报告

    @pytest.mark.integration
    def test_execute_with_error(self, workflow):
        """测试工作流执行错误处理"""
        # Mock失败的任务执行
        workflow.task_tool.execute.side_effect = Exception("测试错误")

        workflow_input = AnalysisWorkflowInput(
            patent_number="CN202310123456.7",
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is False
        assert result.error is not None
        assert "测试错误" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
