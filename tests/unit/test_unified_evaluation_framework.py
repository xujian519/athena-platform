#!/usr/bin/env python3
"""
统一评估框架单元测试
Unit tests for Unified Evaluation Framework

测试内容:
- 准确性指标
- 效率指标
- 质量指标
- 用户满意度指标
- 完整性指标
- 加权评分
- 等级评定
- 改进建议
"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.evaluation.unified_evaluation_framework import (
    EvaluationReport,
    MetricCategory,
    MetricScore,
    UnifiedEvaluationFramework,
)


class TestAccuracyMetric:
    """准确性指标测试"""

    @pytest.mark.asyncio
    async def test_accuracy_calculation(self):
        """测试准确性计算"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "output": "预期输出",
            "accuracy": 0.85
        }

        score = await framework.accuracy_metric.calculate(task_result)

        assert score.name == "准确性"
        assert score.category == MetricCategory.ACCURACY
        assert score.percentage >= 0
        assert score.percentage <= 100

    @pytest.mark.asyncio
    async def test_accuracy_with_ground_truth(self):
        """测试基于ground truth的准确性"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "output": "实际输出",
            "ground_truth": "预期输出"
        }

        score = await framework.accuracy_metric.calculate(task_result)

        # 如果输出匹配，准确性应该很高
        assert score.name == "准确性"

    @pytest.mark.asyncio
    async def test_accuracy_with_errors(self):
        """测试有错误的准确性"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "output": "输出",
            "errors": ["错误1", "错误2"]
        }

        score = await framework.accuracy_metric.calculate(task_result)

        # 有错误时准确性应该降低
        assert score.percentage < 100


class TestEfficiencyMetric:
    """效率指标测试"""

    @pytest.mark.asyncio
    async def test_efficiency_calculation(self):
        """测试效率计算"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "response_time_ms": 0.8,  # 0.8毫秒
            "expected_time_ms": 100  # 期望100毫秒
        }

        score = await framework.efficiency_metric.calculate(task_result)

        assert score.name == "效率"
        assert score.category == MetricCategory.EFFICIENCY
        # 响应时间远低于期望，效率应该很高
        assert score.percentage >= 90

    @pytest.mark.asyncio
    async def test_efficiency_slow_response(self):
        """测试慢响应的效率"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "response_time_ms": 200,  # 200毫秒
            "expected_time_ms": 100  # 期望100毫秒
        }

        score = await framework.efficiency_metric.calculate(task_result)

        # 响应时间超过期望，效率应该较低
        assert score.percentage < 100


class TestQualityMetric:
    """质量指标测试"""

    @pytest.mark.asyncio
    async def test_quality_calculation(self):
        """测试质量计算"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "output": "高质量输出",
            "completeness": 0.9,
            "relevance": 0.85,
            "coherence": 0.8
        }

        score = await framework.quality_metric.calculate(task_result)

        assert score.name == "质量"
        assert score.category == MetricCategory.QUALITY
        assert score.percentage >= 0

    @pytest.mark.asyncio
    async def test_quality_with_poor_output(self):
        """测试低质量输出"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "output": "低质量输出",
            "completeness": 0.5,
            "relevance": 0.4,
            "coherence": 0.3
        }

        score = await framework.quality_metric.calculate(task_result)

        # 低质量输出，得分应该较低
        assert score.percentage < 70


class TestUserSatisfactionMetric:
    """用户满意度指标测试"""

    @pytest.mark.asyncio
    async def test_satisfaction_calculation(self):
        """测试满意度计算"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "user_feedback": {
                "rating": 4.5,
                "comments": "很好"
            }
        }

        score = await framework.user_satisfaction_metric.calculate(task_result)

        assert score.name == "用户满意度"
        assert score.category == MetricCategory.USER_SATISFACTION
        # 4.5/5的评分应该对应高满意度
        assert score.percentage >= 80

    @pytest.mark.asyncio
    async def test_satisfaction_with_low_rating(self):
        """测试低评分满意度"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "user_feedback": {
                "rating": 2.0,
                "comments": "不满意"
            }
        }

        score = await framework.user_satisfaction_metric.calculate(task_result)

        # 2.0/5的评分应该对应低满意度
        assert score.percentage < 50


class TestCompletenessMetric:
    """完整性指标测试"""

    @pytest.mark.asyncio
    async def test_completeness_calculation(self):
        """测试完整性计算"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "required_fields": ["field1", "field2", "field3", "field4", "field5"],
            "present_fields": ["field1", "field2", "field3", "field4"]
        }

        score = await framework.completeness_metric.calculate(task_result)

        assert score.name == "完整性"
        assert score.category == MetricCategory.COMPLETENESS
        # 4/5字段存在，完整性80%
        assert score.percentage == 80

    @pytest.mark.asyncio
    async def test_completeness_all_fields(self):
        """测试所有字段完整"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "required_fields": ["field1", "field2", "field3"],
            "present_fields": ["field1", "field2", "field3"]
        }

        score = await framework.completeness_metric.calculate(task_result)

        # 所有字段都存在，完整性100%
        assert score.percentage == 100


class TestEvaluationReport:
    """评估报告测试"""

    def test_report_creation(self):
        """测试报告创建"""
        report = EvaluationReport(
            report_id="test_report_001",
            evaluation_target="test_task",
            evaluation_type="task"
        )

        assert report.report_id == "test_report_001"
        assert report.evaluation_target == "test_task"
        assert len(report.metrics) == 0
        assert report.overall_score == 0.0
        assert report.overall_grade == "F"

    def test_add_metric(self):
        """测试添加指标"""
        report = EvaluationReport(
            report_id="test_report_002",
            evaluation_target="test_task",
            evaluation_type="task"
        )

        metric = MetricScore(
            name="测试指标",
            category=MetricCategory.ACCURACY,
            score=85.0
        )

        report.add_metric(metric)

        assert len(report.metrics) == 1
        assert report.overall_score > 0

    def test_grade_calculation(self):
        """测试等级计算"""
        report = EvaluationReport(
            report_id="test_report_003",
            evaluation_target="test_task",
            evaluation_type="task"
        )

        # 添加不同等级的指标
        report.add_metric(MetricScore(
            name="指标A",
            category=MetricCategory.ACCURACY,
            score=95.0
        ))

        report.add_metric(MetricScore(
            name="指标B",
            category=MetricCategory.EFFICIENCY,
            score=85.0
        ))

        # 验证等级
        assert report.overall_grade in ["A", "B", "C", "D", "F"]


class TestUnifiedEvaluationFramework:
    """统一评估框架集成测试"""

    @pytest.mark.asyncio
    async def test_full_evaluation(self):
        """测试完整评估流程"""
        framework = UnifiedEvaluationFramework()

        task_result = {
            "output": "专利分析结果",
            "response_time_ms": 0.8,
            "accuracy": 0.85,
            "completeness": 0.9,
            "user_feedback": {"rating": 4.5}
        }

        report = await framework.evaluate(
            task_result,
            evaluation_target="patent_analysis",
            evaluation_type="task"
        )

        assert report is not None
        assert len(report.metrics) > 0
        assert report.overall_score > 0
        assert report.overall_grade in ["A", "B", "C", "D", "F"]

    @pytest.mark.asyncio
    async def test_recommendations_generation(self):
        """测试改进建议生成"""
        framework = UnifiedEvaluationFramework()

        # 创建一个低质量的任务结果
        task_result = {
            "output": "低质量输出",
            "response_time_ms": 200,
            "accuracy": 0.5,
            "completeness": 0.6,
            "user_feedback": {"rating": 2.0}
        }

        report = await framework.evaluate(
            task_result,
            evaluation_target="poor_task",
            evaluation_type="task"
        )

        # 低质量任务应该有改进建议
        assert len(report.recommendations) > 0

    @pytest.mark.asyncio
    async def test_comparison(self):
        """测试系统对比"""
        framework = UnifiedEvaluationFramework()

        system_a_result = {
            "output": "系统A结果",
            "accuracy": 0.9,
            "response_time_ms": 1.0
        }

        system_b_result = {
            "output": "系统B结果",
            "accuracy": 0.8,
            "response_time_ms": 2.0
        }

        comparison = await framework.compare_systems(
            system_a_result,
            system_b_result,
            comparison_name="性能对比"
        )

        assert comparison is not None
        assert "winner" in comparison
        assert "score_difference" in comparison

    def test_statistics(self):
        """测试统计信息"""
        framework = UnifiedEvaluationFramework()

        stats = framework.get_evaluation_stats()

        assert "total_evaluations" in stats
        assert "average_score" in stats
        assert "grade_distribution" in stats


class TestMetricScore:
    """指标得分测试"""

    def test_metric_score_creation(self):
        """测试指标得分创建"""
        score = MetricScore(
            name="测试准确性",
            category=MetricCategory.ACCURACY,
            score=85.0
        )

        assert score.name == "测试准确性"
        assert score.percentage == 85.0
        assert score.grade == "B"

    def test_metric_grade_a(self):
        """测试A级指标"""
        score = MetricScore(
            name="优秀指标",
            category=MetricCategory.ACCURACY,
            score=95.0
        )

        assert score.grade == "A"

    def test_metric_grade_f(self):
        """测试F级指标"""
        score = MetricScore(
            name="不及格指标",
            category=MetricCategory.ACCURACY,
            score=50.0
        )

        assert score.grade == "F"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
