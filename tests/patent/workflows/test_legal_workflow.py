#!/usr/bin/env python3
"""
法律研究工作流测试
Legal Research Workflow Tests

测试法律研究工作流的各个步骤和整体执行。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

from unittest.mock import Mock

import pytest

from core.patents.workflows.legal_workflow import (
    LegalWorkflow,
    LegalWorkflowInput,
)


class TestLegalWorkflow:
    """法律研究工作流测试类"""

    @pytest.fixture
    def workflow(self):
        """创建工作流实例"""
        # Mock TaskTool
        mock_task_tool = Mock()
        mock_task_tool.execute.return_value = {
            "success": True,
            "task_id": "test-task-789",
            "status": "completed",
            "agent_id": "legal-agent-789",
            "model": "opus",
        }

        return LegalWorkflow(task_tool=mock_task_tool)

    def test_initialization(self, workflow):
        """测试工作流初始化"""
        assert workflow is not None
        assert workflow.task_tool is not None
        assert len(workflow.workflow_steps) == 5

    def test_get_workflow_config(self, workflow):
        """测试获取工作流配置"""
        config = workflow.get_workflow_config()
        assert config["name"] == "法律研究工作流"
        assert "steps" in config
        assert "config" in config

    def test_get_supported_query_types(self, workflow):
        """测试获取支持的查询类型"""
        types = workflow.get_supported_query_types()
        assert "statute" in types
        assert "case" in types
        assert "interpretation" in types
        assert len(types) == 3

    def test_get_supported_case_types(self, workflow):
        """测试获取支持的案例类型"""
        case_types = workflow.get_supported_case_types()
        assert "infringement" in case_types
        assert "invalidation" in case_types
        assert "administrative" in case_types
        assert len(case_types) == 3

    @pytest.mark.unit
    def test_step_legal_query_parser(self, workflow):
        """测试步骤1: 法律问题解析"""
        parsed_query = workflow._step_legal_query_parser("分析专利侵权判例")
        assert parsed_query is not None
        assert "original_query" in parsed_query
        assert parsed_query["original_query"] == "分析专利侵权判例"

    @pytest.mark.unit
    def test_step_statute_lookup(self, workflow):
        """测试步骤2: 法规检索"""
        parsed_query = {
            "original_query": "专利侵权",
            "query_type": "case",
        }

        statutes = workflow._step_statute_lookup(parsed_query, "statute")

        assert statutes is not None
        assert len(statutes) > 0
        assert "statute_id" in statutes[0]

    @pytest.mark.unit
    def test_step_case_law_search(self, workflow):
        """测试步骤3: 案例法检索"""
        parsed_query = {
            "original_query": "专利侵权",
        }

        cases = workflow._step_case_law_search(
            parsed_query,
            ["infringement", "invalidation"],
            {"start": "2020-01-01", "end": "2024-12-31"},
        )

        assert cases is not None
        assert len(cases) > 0
        assert "case_id" in cases[0]

    @pytest.mark.unit
    def test_step_legal_reasoning(self, workflow):
        """测试步骤4: 法理分析"""
        statutes = [
            {"statute_id": "专利法第25条", "content": "法律条文内容"},
        ]
        cases = [
            {"case_id": "案例001", "summary": "案例摘要"},
        ]

        legal_analysis = workflow._step_legal_reasoning(statutes, cases)

        assert legal_analysis is not None
        assert "statute_application" in legal_analysis
        assert "case_consistency" in legal_analysis

    @pytest.mark.unit
    def test_step_opinion_generator(self, workflow):
        """测试步骤5: 法律意见生成"""
        parsed_query = {
            "original_query": "专利侵权分析",
        }
        legal_analysis = {
            "statute_application": "法律条文应用",
            "case_consistency": "案例一致性",
        }

        opinion = workflow._step_opinion_generator(parsed_query, legal_analysis)

        assert opinion is not None
        assert "content" in opinion
        assert "# 法律意见书" in opinion["content"]

    @pytest.mark.unit
    def test_perform_trend_analysis(self, workflow):
        """测试趋势分析"""
        cases = [
            {"case_id": "案例001", "date": "2023-05-15"},
            {"case_id": "案例002", "date": "2023-06-20"},
        ]

        trend_analysis = workflow._perform_trend_analysis(cases)

        assert trend_analysis is not None
        assert "trend_overview" in trend_analysis

    @pytest.mark.integration
    def test_execute_comprehensive_legal_research(self, workflow):
        """测试执行综合法律研究"""
        workflow_input = LegalWorkflowInput(
            legal_query="分析专利侵权判例",
            query_type="case",
            case_types=["infringement", "invalidation"],
            include_trend_analysis=True,
            generate_opinion=True,
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is True
        assert result.task_id is not None
        assert result.legal_query == "分析专利侵权判例"
        assert len(result.steps_completed) == 5
        assert result.statutes is not None
        assert result.cases is not None
        assert result.legal_analysis is not None
        assert result.legal_opinion is not None
        assert result.trend_analysis is not None

    @pytest.mark.integration
    def test_execute_statute_only(self, workflow):
        """测试执行仅法规检索"""
        workflow_input = LegalWorkflowInput(
            legal_query="专利法第25条",
            query_type="statute",
            include_trend_analysis=False,
            generate_opinion=False,
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is True
        assert result.query_type == "statute"

    @pytest.mark.integration
    def test_execute_with_error(self, workflow):
        """测试工作流执行错误处理"""
        # Mock失败的任务执行
        workflow.task_tool.execute.side_effect = Exception("法律检索错误")

        workflow_input = LegalWorkflowInput(
            legal_query="专利侵权",
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is False
        assert result.error is not None
        assert "法律检索错误" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
