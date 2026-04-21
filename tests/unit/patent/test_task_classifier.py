"""
专利任务分类系统单元测试
Unit tests for Patent Task Classifier

基于专利NLP综述论文
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock

from core.patents.ai_services.task_classifier import (
    ExecutionPriority,
    PatentTaskClassifier,
    PatentTaskType,
    SubTask,
    TaskClassificationResult,
    TaskComplexity,
    WorkflowStage,
    WorkflowStep,
    classify_patent_task,
    format_classification_report,
    get_workflow_for_task,
)

# ==================== 枚举测试 ====================

class TestEnums:
    """枚举类型测试"""

    def test_patent_task_type_values(self):
        """测试专利任务类型枚举"""
        assert PatentTaskType.PRIOR_ART_SEARCH.value == "prior_art_search"
        assert PatentTaskType.INFRINGEMENT_ANALYSIS.value == "infringement_analysis"
        assert PatentTaskType.CLAIM_DRAFTING.value == "claim_drafting"

    def test_task_complexity_values(self):
        """测试任务复杂度枚举"""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"

    def test_workflow_stage_values(self):
        """测试工作流阶段枚举"""
        assert WorkflowStage.DISCOVERY.value == "discovery"
        assert WorkflowStage.ANALYSIS.value == "analysis"
        assert WorkflowStage.VALIDATION.value == "validation"

    def test_execution_priority_values(self):
        """测试执行优先级枚举"""
        assert ExecutionPriority.URGENT.value == 1
        assert ExecutionPriority.HIGH.value == 2
        assert ExecutionPriority.NORMAL.value == 3


# ==================== 数据结构测试 ====================

class TestSubTask:
    """SubTask 数据结构测试"""

    def test_subtask_creation(self):
        """测试子任务创建"""
        subtask = SubTask(
            subtask_id="ST1",
            task_type=PatentTaskType.PRIOR_ART_SEARCH,
            description="检索现有技术",
            dependencies=[],
            estimated_time=5.0,
            required_tools=["patent_db"]
        )
        assert subtask.subtask_id == "ST1"
        assert subtask.task_type == PatentTaskType.PRIOR_ART_SEARCH
        assert subtask.estimated_time == 5.0

    def test_subtask_with_dependencies(self):
        """测试带依赖的子任务"""
        subtask = SubTask(
            subtask_id="ST2",
            task_type=PatentTaskType.NOVELTY_ANALYSIS,
            description="分析新颖性",
            dependencies=["ST1"],
            estimated_time=10.0
        )
        assert len(subtask.dependencies) == 1
        assert "ST1" in subtask.dependencies

    def test_subtask_to_dict(self):
        """测试子任务序列化"""
        subtask = SubTask(
            subtask_id="ST3",
            task_type=PatentTaskType.QUALITY_ASSESSMENT,
            description="质量检查",
            priority=ExecutionPriority.HIGH
        )
        result = subtask.to_dict()
        assert result["subtask_id"] == "ST3"
        assert result["priority"] == 2


class TestWorkflowStep:
    """WorkflowStep 数据结构测试"""

    def test_workflow_step_creation(self):
        """测试工作流步骤创建"""
        step = WorkflowStep(
            step_id="WS1",
            stage=WorkflowStage.DISCOVERY,
            subtasks=[],
            description="发现阶段",
            order=1
        )
        assert step.step_id == "WS1"
        assert step.stage == WorkflowStage.DISCOVERY

    def test_workflow_step_to_dict(self):
        """测试工作流步骤序列化"""
        subtask = SubTask("ST1", PatentTaskType.PRIOR_ART_SEARCH, "检索")
        step = WorkflowStep(
            step_id="WS1",
            stage=WorkflowStage.ANALYSIS,
            subtasks=[subtask],
            order=2
        )
        result = step.to_dict()
        assert result["stage"] == "analysis"
        assert len(result["subtasks"]) == 1


class TestTaskClassificationResult:
    """TaskClassificationResult 数据结构测试"""

    def test_result_creation(self):
        """测试分类结果创建"""
        result = TaskClassificationResult(
            classification_id="classify_001",
            primary_task_type=PatentTaskType.INFRINGEMENT_ANALYSIS,
            complexity=TaskComplexity.COMPLEX
        )
        assert result.classification_id == "classify_001"
        assert result.primary_task_type == PatentTaskType.INFRINGEMENT_ANALYSIS

    def test_result_with_full_data(self):
        """测试完整数据的结果"""
        result = TaskClassificationResult(
            classification_id="classify_002",
            primary_task_type=PatentTaskType.SPECIFICATION_DRAFTING,
            secondary_task_types=[PatentTaskType.CLAIM_DRAFTING],
            complexity=TaskComplexity.VERY_COMPLEX,
            detected_intent="撰写专利说明书",
            intent_confidence=0.9,
            entities={"patent_number": "CN123456"},
            subtasks=[
                SubTask("ST1", PatentTaskType.SPECIFICATION_DRAFTING, "任务1")
            ],
            estimated_total_time=30.0
        )
        assert len(result.secondary_task_types) == 1
        assert len(result.entities) == 1
        assert len(result.subtasks) == 1

    def test_result_to_dict(self):
        """测试结果序列化"""
        result = TaskClassificationResult(
            classification_id="classify_003",
            primary_task_type=PatentTaskType.PATENT_QA,
            complexity=TaskComplexity.SIMPLE,
            detected_intent="专利问答",
            intent_confidence=0.85
        )
        data = result.to_dict()
        assert data["classification_id"] == "classify_003"
        assert data["complexity"] == "simple"


# ==================== PatentTaskClassifier 测试 ====================

class TestPatentTaskClassifier:
    """PatentTaskClassifier 核心测试"""

    def test_classifier_initialization(self):
        """测试分类器初始化"""
        classifier = PatentTaskClassifier()
        assert classifier.llm_manager is None
        assert hasattr(classifier, 'INTENT_KEYWORDS')
        assert hasattr(classifier, 'WORKFLOW_TEMPLATES')

    def test_classifier_with_llm_manager(self):
        """测试带LLM管理器的初始化"""
        mock_llm = MagicMock()
        classifier = PatentTaskClassifier(llm_manager=mock_llm)
        assert classifier.llm_manager == mock_llm

    def test_rule_based_classification_prior_art(self):
        """测试规则分类 - 现有技术检索"""
        classifier = PatentTaskClassifier()
        task_type = classifier._rule_based_classification(
            "请帮我检索现有技术"
        )
        assert task_type == PatentTaskType.PRIOR_ART_SEARCH

    def test_rule_based_classification_infringement(self):
        """测试规则分类 - 侵权分析"""
        classifier = PatentTaskClassifier()
        task_type = classifier._rule_based_classification(
            "这个产品是否侵权了我的专利权？"
        )
        assert task_type == PatentTaskType.INFRINGEMENT_ANALYSIS

    def test_rule_based_classification_drafting(self):
        """测试规则分类 - 撰写"""
        classifier = PatentTaskClassifier()
        task_type = classifier._rule_based_classification(
            "帮我撰写权利要求书"
        )
        assert task_type == PatentTaskType.CLAIM_DRAFTING

    def test_rule_based_classification_unknown(self):
        """测试规则分类 - 未知"""
        classifier = PatentTaskClassifier()
        task_type = classifier._rule_based_classification(
            "今天天气怎么样"
        )
        assert task_type == PatentTaskType.UNKNOWN

    def test_extract_entities_patent_number(self):
        """测试实体提取 - 专利号"""
        classifier = PatentTaskClassifier()

        # 中国专利号
        entities = classifier._extract_entities("查询专利CN12345678A")
        assert "patent_number" in entities

        # 美国专利号
        entities = classifier._extract_entities("查看US1234567专利")
        assert "patent_number" in entities

    def test_extract_entities_ipc(self):
        """测试实体提取 - IPC分类号"""
        classifier = PatentTaskClassifier()
        entities = classifier._extract_entities(
            "查询H04L 29/06分类下的专利"
        )
        assert "ipc_class" in entities

    def test_extract_entities_year(self):
        """测试实体提取 - 年份"""
        classifier = PatentTaskClassifier()
        entities = classifier._extract_entities("查询2023年的专利")
        assert "year" in entities

    def test_estimate_complexity_simple(self):
        """测试复杂度估计 - 简单"""
        classifier = PatentTaskClassifier()
        complexity = classifier._estimate_complexity(
            "查询专利",
            PatentTaskType.PATENT_LOOKUP
        )
        assert complexity == TaskComplexity.SIMPLE

    def test_estimate_complexity_complex(self):
        """测试复杂度估计 - 复杂"""
        classifier = PatentTaskClassifier()
        complexity = classifier._estimate_complexity(
            "请详细分析这个产品是否侵犯了以下专利的权利要求，并给出详细的法律意见和可能的应对策略",
            PatentTaskType.INFRINGEMENT_ANALYSIS
        )
        assert complexity == TaskComplexity.COMPLEX

    def test_heuristic_decomposition_prior_art(self):
        """测试启发式分解 - 现有技术检索"""
        classifier = PatentTaskClassifier()
        subtasks = classifier._heuristic_decomposition(
            PatentTaskType.PRIOR_ART_SEARCH
        )
        assert len(subtasks) >= 1
        assert all(isinstance(s, SubTask) for s in subtasks)

    def test_heuristic_decomposition_infringement(self):
        """测试启发式分解 - 侵权分析"""
        classifier = PatentTaskClassifier()
        subtasks = classifier._heuristic_decomposition(
            PatentTaskType.INFRINGEMENT_ANALYSIS
        )
        assert len(subtasks) >= 1

    def test_map_to_workflow(self):
        """测试工作流映射"""
        classifier = PatentTaskClassifier()
        subtasks = [SubTask("ST1", PatentTaskType.PRIOR_ART_SEARCH, "任务")]
        workflow = classifier._map_to_workflow(
            PatentTaskType.PRIOR_ART_SEARCH, subtasks
        )
        assert len(workflow) >= 1
        assert all(isinstance(w, WorkflowStep) for w in workflow)

    def test_recommend_tools(self):
        """测试工具推荐"""
        classifier = PatentTaskClassifier()

        tools = classifier._recommend_tools(PatentTaskType.PRIOR_ART_SEARCH)
        assert len(tools) > 0

        tools = classifier._recommend_tools(PatentTaskType.SPECIFICATION_DRAFTING)
        assert len(tools) > 0

    def test_get_task_workflow(self):
        """测试获取任务工作流"""
        classifier = PatentTaskClassifier()
        workflow = classifier.get_task_workflow(PatentTaskType.PRIOR_ART_SEARCH)
        assert len(workflow) >= 1
        assert WorkflowStage.RETRIEVAL in workflow or WorkflowStage.DISCOVERY in workflow


# ==================== 异步方法测试 ====================

@pytest.mark.asyncio
class TestAsyncMethods:
    """异步方法测试"""

    async def test_classify_no_llm(self):
        """测试无LLM时的分类"""
        classifier = PatentTaskClassifier()
        result = await classifier.classify("请帮我检索现有技术")
        assert isinstance(result, TaskClassificationResult)
        assert result.primary_task_type == PatentTaskType.PRIOR_ART_SEARCH

    async def test_classify_infringement(self):
        """测试侵权分析分类"""
        classifier = PatentTaskClassifier()
        result = await classifier.classify("分析是否侵权")
        assert result.primary_task_type == PatentTaskType.INFRINGEMENT_ANALYSIS

    async def test_batch_classify(self):
        """测试批量分类"""
        classifier = PatentTaskClassifier()
        queries = [
            "检索现有技术",
            "撰写权利要求",
            "分析侵权"
        ]
        results = await classifier.batch_classify(queries)
        assert len(results) == 3
        assert all(isinstance(r, TaskClassificationResult) for r in results)


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_classify_patent_task(self):
        """测试便捷分类函数"""
        result = await classify_patent_task(
            query="请帮我分析专利的新颖性",
            llm_manager=None
        )
        assert isinstance(result, TaskClassificationResult)

    def test_get_workflow_for_task(self):
        """测试获取工作流函数"""
        workflow = get_workflow_for_task(PatentTaskType.PRIOR_ART_SEARCH)
        assert isinstance(workflow, list)
        assert len(workflow) >= 1

    def test_format_classification_report(self):
        """测试格式化报告"""
        result = TaskClassificationResult(
            classification_id="test_001",
            primary_task_type=PatentTaskType.INFRINGEMENT_ANALYSIS,
            complexity=TaskComplexity.COMPLEX,
            detected_intent="侵权分析",
            intent_confidence=0.9,
            entities={"patent_number": "CN123456"},
            subtasks=[
                SubTask("ST1", PatentTaskType.CLAIM_ANALYSIS, "解析权利要求")
            ],
            workflow_steps=[
                WorkflowStep("WS1", WorkflowStage.DISCOVERY, [], order=1)
            ],
            recommended_tools=["claim_parser", "comparison_tool"]
        )
        report = format_classification_report(result)
        assert "专利任务分类报告" in report
        assert "infringement_analysis" in report
        assert "CN123456" in report


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """边界条件测试"""

    def test_empty_query(self):
        """测试空查询"""
        classifier = PatentTaskClassifier()
        task_type = classifier._rule_based_classification("")
        assert task_type == PatentTaskType.UNKNOWN

    def test_very_long_query(self):
        """测试超长查询"""
        classifier = PatentTaskClassifier()
        long_query = "专利检索" * 1000
        task_type = classifier._rule_based_classification(long_query)
        assert isinstance(task_type, PatentTaskType)

    def test_multiple_keywords(self):
        """测试多个关键词"""
        classifier = PatentTaskClassifier()
        # 包含多个任务关键词
        query = "请帮我检索现有技术并分析是否侵权"
        task_type = classifier._rule_based_classification(query)
        # 应该返回得分最高的类型
        assert isinstance(task_type, PatentTaskType)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
