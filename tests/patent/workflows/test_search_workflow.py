#!/usr/bin/env python3
"""
专利检索工作流测试
Patent Search Workflow Tests

测试专利检索工作流的各个步骤和整体执行。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

from unittest.mock import Mock

import pytest

from core.patent.workflows.search_workflow import (
    SearchWorkflow,
    SearchWorkflowInput,
)


class TestSearchWorkflow:
    """专利检索工作流测试类"""

    @pytest.fixture
    def workflow(self):
        """创建工作流实例"""
        # Mock TaskTool
        mock_task_tool = Mock()
        mock_task_tool.execute.return_value = {
            "success": True,
            "task_id": "test-task-456",
            "status": "completed",
            "agent_id": "search-agent-456",
            "model": "haiku",
        }

        return SearchWorkflow(task_tool=mock_task_tool)

    def test_initialization(self, workflow):
        """测试工作流初始化"""
        assert workflow is not None
        assert workflow.task_tool is not None
        assert len(workflow.workflow_steps) == 5

    def test_get_workflow_config(self, workflow):
        """测试获取工作流配置"""
        config = workflow.get_workflow_config()
        assert config["name"] == "专利检索工作流"
        assert "steps" in config
        assert "config" in config

    def test_get_supported_data_sources(self, workflow):
        """测试获取支持的数据源"""
        sources = workflow.get_supported_data_sources()
        assert "local" in sources
        assert "online" in sources
        assert len(sources) == 2

    def test_get_supported_export_formats(self, workflow):
        """测试获取支持的导出格式"""
        formats = workflow.get_supported_export_formats()
        assert "csv" in formats
        assert "json" in formats
        assert "xml" in formats
        assert "pdf" in formats
        assert len(formats) == 4

    @pytest.mark.unit
    def test_step_search_strategy_builder(self, workflow):
        """测试步骤1: 检索策略构建"""
        search_strategy = workflow._step_search_strategy_builder(
            "量子计算",
            ["local", "online"],
        )
        assert search_strategy is not None
        assert "query" in search_strategy
        assert search_strategy["query"] == "量子计算"

    @pytest.mark.unit
    def test_step_multi_source_search(self, workflow):
        """测试步骤2: 多源检索执行"""
        search_strategy = {
            "query": "量子计算",
            "data_sources": ["local"],
            "max_results": 50,
        }

        results = workflow._step_multi_source_search(
            search_strategy,
            ["local"],
        )

        assert results is not None
        assert len(results) > 0
        assert results[0]["source"] == "local"
        assert "results" in results[0]

    @pytest.mark.unit
    def test_step_result_deduplication(self, workflow):
        """测试步骤3: 结果去重和排序"""
        search_results = [
            {
                "source": "local",
                "results": [
                    {"patent_number": "CN123456", "title": "专利1"},
                    {"patent_number": "CN123456", "title": "重复专利"},
                    {"patent_number": "CN789012", "title": "专利2"},
                ],
            },
            {
                "source": "online",
                "results": [
                    {"patent_number": "CN345678", "title": "专利3"},
                ],
            },
        ]

        deduped_results = workflow._step_result_deduplication(search_results)

        assert deduped_results is not None
        # 检查去重 (CN123456应该只出现一次)
        patent_numbers = [r.get("patent_number") for r in deduped_results]
        assert patent_numbers.count("CN123456") == 1
        assert len(deduped_results) == 3  # 去重后应该有3条

    @pytest.mark.unit
    def test_step_relevance_filtering(self, workflow):
        """测试步骤4: 相关性过滤"""
        results = [
            {"patent_number": "CN123456", "relevance": 0.95},
            {"patent_number": "CN789012", "relevance": 0.85},
            {"patent_number": "CN345678", "relevance": 0.75},
        ]

        filtered_results = workflow._step_relevance_filtering(results, max_results=2)

        assert filtered_results is not None
        assert len(filtered_results) <= 2

    @pytest.mark.unit
    def test_step_result_export_csv(self, workflow):
        """测试步骤5: 结果导出 - CSV格式"""
        results = [
            {"patent_number": "CN123456", "title": "专利1"},
        ]

        result = workflow._step_result_export(
            results,
            export_format="csv",
            export_path="/tmp/test.csv",
        )

        assert result is not None
        assert "content" in result
        assert "path" in result
        assert result["format"] == "csv"

    @pytest.mark.unit
    def test_step_result_export_json(self, workflow):
        """测试步骤5: 结果导出 - JSON格式"""
        results = [
            {"patent_number": "CN123456", "title": "专利1"},
        ]

        result = workflow._step_result_export(
            results,
            export_format="json",
            export_path="/tmp/test.json",
        )

        assert result is not None
        assert "content" in result
        assert "path" in result
        assert result["format"] == "json"

    @pytest.mark.integration
    def test_execute_comprehensive_search(self, workflow):
        """测试执行综合检索工作流"""
        workflow_input = SearchWorkflowInput(
            query="量子计算",
            data_sources=["local", "online"],
            max_results=50,
            export_format="csv",
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is True
        assert result.task_id is not None
        assert result.query == "量子计算"
        assert len(result.steps_completed) == 5
        assert result.results is not None
        assert result.total_count > 0

    @pytest.mark.integration
    def test_execute_local_only(self, workflow):
        """测试执行仅本地检索"""
        workflow_input = SearchWorkflowInput(
            query="量子计算",
            data_sources=["local"],  # 仅本地
            max_results=20,
            export_format="json",
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is True
        assert len(result.data_sources) == 1
        assert result.data_sources[0] == "local"

    @pytest.mark.integration
    def test_execute_with_error(self, workflow):
        """测试工作流执行错误处理"""
        # Mock失败的任务执行
        workflow.task_tool.execute.side_effect = Exception("检索错误")

        workflow_input = SearchWorkflowInput(
            query="量子计算",
        )

        result = workflow.execute(workflow_input)

        assert result is not None
        assert result.success is False
        assert result.error is not None
        assert "检索错误" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
