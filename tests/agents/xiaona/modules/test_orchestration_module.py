"""
编排模块测试

测试OrchestrationModule的完整流程编排功能。
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from core.framework.agents.xiaona.modules.orchestration_module import (
    OrchestrationModule,
    OrchestrationProgress,
    TaskResult,
    TaskStatus,
)


class TestTaskResult:
    """测试TaskResult数据类"""

    def test_task_result_creation(self):
        """测试创建任务结果"""
        result = TaskResult(
            task_name="test_task",
            status=TaskStatus.COMPLETED,
            result={"key": "value"},
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.5,
        )

        assert result.task_name == "test_task"
        assert result.status == TaskStatus.COMPLETED
        assert result.result == {"key": "value"}
        assert result.duration == 1.5

    def test_task_result_to_dict(self):
        """测试任务结果转字典"""
        result = TaskResult(
            task_name="test_task",
            status=TaskStatus.COMPLETED,
            result={"key": "value"},
        )

        result_dict = result.to_dict()
        assert result_dict["task_name"] == "test_task"
        assert result_dict["status"] == "completed"
        assert result_dict["result"] == {"key": "value"}


class TestOrchestrationProgress:
    """测试OrchestrationProgress数据类"""

    def test_progress_initialization(self):
        """测试进度初始化"""
        progress = OrchestrationProgress(total_steps=5)

        assert progress.total_steps == 5
        assert progress.completed_steps == 0
        assert progress.current_step == ""
        assert len(progress.task_results) == 0

    def test_add_result(self):
        """测试添加结果"""
        progress = OrchestrationProgress(total_steps=5)
        result = TaskResult(
            task_name="test",
            status=TaskStatus.COMPLETED,
        )

        progress.add_result(result)

        assert progress.completed_steps == 1
        assert len(progress.task_results) == 1

    def test_add_failed_result(self):
        """测试添加失败结果不影响计数"""
        progress = OrchestrationProgress(total_steps=5)
        result = TaskResult(
            task_name="test",
            status=TaskStatus.FAILED,
        )

        progress.add_result(result)

        assert progress.completed_steps == 0  # 失败不计数

    def test_get_progress_summary(self):
        """测试获取进度摘要"""
        progress = OrchestrationProgress(total_steps=4)
        progress.current_step = "测试步骤"
        progress.completed_steps = 2

        summary = progress.get_progress_summary()

        assert summary["total_steps"] == 4
        assert summary["completed_steps"] == 2
        assert summary["progress_percent"] == 50.0
        assert summary["current_step"] == "测试步骤"


class TestOrchestrationModule:
    """测试编排模块"""

    @pytest.fixture
    def module(self):
        """创建编排模块实例"""
        return OrchestrationModule()

    @pytest.fixture
    def mock_disclosure_data(self):
        """模拟交底书数据"""
        return {
            "title": "测试发明",
            "technical_field": "机械领域",
            "background_art": "现有技术描述",
            "summary": "技术方案摘要",
            "detailed_description": "具体实施方式",
        }

    @pytest.fixture
    def mock_office_action(self):
        """模拟审查意见"""
        return {
            "patent_number": "CN123456789A",
            "rejections": [
                {
                    "type": "novelty",
                    "claims": [1, 2],
                    "reason": "缺乏新颖性",
                }
            ],
            "citations": [
                {"number": "CN111111111A", "relevance": "A"},
                {"number": "CN222222222U", "relevance": "B"},
            ],
            "deadline": "2026-06-01",
        }

    @pytest.mark.asyncio
    async def test_draft_full_application_success(self, module, mock_disclosure_data):
        """测试完整申请流程成功"""
        # 模拟PatentDraftingProxy
        mock_proxy = AsyncMock()
        mock_proxy.analyze_disclosure.return_value = {
            "title": "测试发明",
            "technical_field": "机械领域",
            "innovation_points": ["创新点1", "创新点2"],
        }
        mock_proxy.assess_patentability.return_value = {
            "novelty": "中等",
            "creativity": "中等",
            "practical_applicability": "高",
        }
        mock_proxy.draft_claims.return_value = {
            "independent_claims": ["1. 一种装置..."],
            "dependent_claims": ["2. 根据权利要求1..."],
        }
        mock_proxy.draft_specification.return_value = {
            "sections": {
                "technical_field": "本发明涉及...",
                "background_art": "现有技术...",
                "summary": "本发明提供...",
                "detailed_description": "具体实施方式...",
            },
        }
        mock_proxy.review_adequacy.return_value = {
            "adequacy_score": 0.85,
            "issues": [],
        }
        mock_proxy.detect_common_errors.return_value = {
            "errors": [],
            "warnings": [],
        }

        with patch.object(module, '_get_drafting_proxy', return_value=mock_proxy):
            result = await module.draft_full_application(mock_disclosure_data)

        assert result["success"] is True
        assert result["analysis_report"] is not None
        assert result["patentability_report"] is not None
        assert result["claims"] is not None
        assert result["specification"] is not None
        assert result["adequacy_review"] is not None
        assert result["error_report"] is not None

        # 验证所有方法都被调用
        mock_proxy.analyze_disclosure.assert_called_once()
        mock_proxy.assess_patentability.assert_called_once()
        mock_proxy.draft_claims.assert_called_once()
        mock_proxy.draft_specification.assert_called_once()
        mock_proxy.review_adequacy.assert_called_once()
        mock_proxy.detect_common_errors.assert_called_once()

    @pytest.mark.asyncio
    async def test_draft_full_application_with_failure(self, module, mock_disclosure_data):
        """测试完整申请流程中的失败处理"""
        mock_proxy = AsyncMock()
        mock_proxy.analyze_disclosure.return_value = {
            "title": "测试发明",
        }
        mock_proxy.assess_patentability.return_value = {
            "novelty": "中等",
        }
        mock_proxy.draft_claims.side_effect = Exception("撰写失败")

        with patch.object(module, '_get_drafting_proxy', return_value=mock_proxy):
            result = await module.draft_full_application(mock_disclosure_data)

        assert result["success"] is False
        assert "撰写失败" in result["error"]
        assert result["analysis_report"] is not None  # 前面的步骤应该完成
        assert result["claims"] is None  # 失败的步骤应该为空

    @pytest.mark.asyncio
    async def test_orchestrate_response_success(self, module, mock_office_action):
        """测试答复流程编排成功"""
        # 模拟各代理
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_office_action.return_value = {
            "rejections": ["新颖性问题"],
            "keywords": ["关键词1", "关键词2"],
        }
        mock_analyzer.analyze_citations.return_value = {
            "citations_analyzed": 2,
            "key_citations": ["CN111111111A"],
        }

        mock_retriever = AsyncMock()
        mock_retriever.search_patents.return_value = {
            "search_results": [{"number": "CN333333333A"}],
            "total": 1,
        }

        mock_writer = AsyncMock()
        mock_writer.draft_response.return_value = {
            "response_content": "答复意见内容",
            "arguments": ["争辩理由1"],
        }
        mock_writer.review_response.return_value = {
            "quality_score": 0.9,
            "issues": [],
        }

        with patch.object(module, '_get_analyzer_agent', return_value=mock_analyzer), \
             patch.object(module, '_get_retriever_agent', return_value=mock_retriever), \
             patch.object(module, '_get_writer_agent', return_value=mock_writer):

            result = await module.orchestrate_response(
                mock_office_action,
                search_existing_art=True,
            )

        assert result["success"] is True
        assert result["office_action_analysis"] is not None
        assert result["citation_analysis"] is not None
        assert result["prior_art_search"] is not None
        assert result["response_draft"] is not None
        assert result["response_review"] is not None

    @pytest.mark.asyncio
    async def test_orchestrate_response_without_search(self, module, mock_office_action):
        """测试不检索现有技术的答复流程"""
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_office_action.return_value = {"rejections": []}
        mock_analyzer.analyze_citations.return_value = {"citations_analyzed": 0}

        mock_writer = AsyncMock()
        mock_writer.draft_response.return_value = {"response_content": "内容"}
        mock_writer.review_response.return_value = {"quality_score": 0.8}

        with patch.object(module, '_get_analyzer_agent', return_value=mock_analyzer), \
             patch.object(module, '_get_writer_agent', return_value=mock_writer):

            result = await module.orchestrate_response(
                mock_office_action,
                search_existing_art=False,
            )

        assert result["success"] is True
        assert result["prior_art_search"] is None  # 未检索应该为空

    @pytest.mark.asyncio
    async def test_execute_sequential(self, module):
        """测试串行执行"""
        task1 = AsyncMock(return_value="result1")
        task2 = AsyncMock(return_value="result2")
        task3 = AsyncMock(return_value="result3")

        tasks = [task1, task2, task3]
        task_names = ["task1", "task2", "task3"]

        results = await module.execute_sequential(tasks, task_names)

        assert len(results) == 3
        assert all(r.status == TaskStatus.COMPLETED for r in results)
        assert results[0].result == "result1"
        assert results[1].result == "result2"
        assert results[2].result == "result3"

        # 验证执行顺序
        task1.assert_called_once()
        task2.assert_called_once()
        task3.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sequential_with_failure(self, module):
        """测试串行执行中的失败处理"""
        task1 = AsyncMock(return_value="result1")
        task2 = AsyncMock(side_effect=Exception("失败"))
        task3 = AsyncMock(return_value="result3")

        tasks = [task1, task2, task3]
        task_names = ["task1", "task2", "task3"]

        results = await module.execute_sequential(tasks, task_names)

        assert len(results) == 2  # 失败后停止
        assert results[0].status == TaskStatus.COMPLETED
        assert results[1].status == TaskStatus.FAILED
        assert "失败" in results[1].error

        # task3不应该被调用
        task3.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_parallel(self, module):
        """测试并行执行"""
        task1 = AsyncMock(return_value="result1")
        task2 = AsyncMock(return_value="result2")
        task3 = AsyncMock(return_value="result3")

        tasks = [task1, task2, task3]
        task_names = ["task1", "task2", "task3"]

        results = await module.execute_parallel(tasks, task_names)

        assert len(results) == 3
        assert all(r.status == TaskStatus.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_execute_parallel_with_partial_failure(self, module):
        """测试并行执行中的部分失败"""
        task1 = AsyncMock(return_value="result1")
        task2 = AsyncMock(side_effect=Exception("失败"))
        task3 = AsyncMock(return_value="result3")

        tasks = [task1, task2, task3]
        task_names = ["task1", "task2", "task3"]

        results = await module.execute_parallel(tasks, task_names)

        assert len(results) == 3
        assert results[0].status == TaskStatus.COMPLETED
        assert results[1].status == TaskStatus.FAILED
        assert results[2].status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_progress_callback(self, module, mock_disclosure_data):
        """测试进度回调"""
        mock_proxy = AsyncMock()
        mock_proxy.analyze_disclosure.return_value = {"title": "测试"}
        mock_proxy.assess_patentability.return_value = {"novelty": "中等"}
        mock_proxy.draft_claims.return_value = {"claims": []}
        mock_proxy.draft_specification.return_value = {"spec": ""}
        mock_proxy.review_adequacy.return_value = {"score": 0.8}
        mock_proxy.detect_common_errors.return_value = {"errors": []}

        callback_calls = []

        async def mock_callback(step_name, progress):
            callback_calls.append((step_name, progress))

        with patch.object(module, '_get_drafting_proxy', return_value=mock_proxy):
            result = await module.draft_full_application(
                mock_disclosure_data,
                progress_callback=mock_callback,
            )

        assert result["success"] is True
        assert len(callback_calls) >= 6  # 至少6个步骤的回调
        assert callback_calls[-1][1] == 1.0  # 最后应该是100%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
