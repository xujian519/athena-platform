#!/usr/bin/env python3
"""
小诺评估反馈系统测试
Xiaonuo Feedback System Tests

测试反馈系统的功能:
- 明确反馈收集
- 隐式反馈推断
- 服务质量评估
- 改进计划生成
- 数据持久化

作者: 小诺·双鱼座
创建时间: 2025-12-18
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.evaluation.xiaonuo_feedback_system import (
    FeedbackItem,
    FeedbackType,
    QualityMetrics,
    SatisfactionLevel,
    ServiceMetrics,
    XiaonuoFeedbackSystem,
)


# ========== 测试数据 ==========

@pytest.fixture
def temp_feedback_dir():
    """创建临时反馈目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_dir = Path(tmpdir) / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        yield feedback_dir


@pytest.fixture
def feedback_system(temp_feedback_dir):
    """创建反馈系统实例"""
    system = XiaonuoFeedbackSystem()
    # 更新数据路径到临时目录
    system.feedback_data_path = str(temp_feedback_dir / "feedback.json")
    system.metrics_data_path = str(temp_feedback_dir / "metrics.json")
    return system


# ========== 明确反馈测试 ==========

class TestExplicitFeedback:
    """明确反馈测试"""

    def test_collect_explicit_feedback_high_satisfaction(self, feedback_system):
        """测试收集高满意度反馈"""
        feedback_id = feedback_system.collect_explicit_feedback(
            satisfaction=5,
            content="非常好的回答，解决了我的问题",
            context={"task": "专利检索"},
        )

        assert feedback_id is not None
        assert feedback_id.startswith("fb_")

        # 验证反馈被记录
        assert len(feedback_system.feedback_history) == 1
        feedback = feedback_system.feedback_history[0]
        assert feedback.satisfaction_level == SatisfactionLevel.VERY_SATISFIED
        assert feedback.feedback_type == FeedbackType.EXPLICIT
        assert "非常好" in feedback.content

    def test_collect_explicit_feedback_low_satisfaction(self, feedback_system):
        """测试收集低满意度反馈"""
        feedback_id = feedback_system.collect_explicit_feedback(
            satisfaction=1,
            content="回答不准确，没有帮助",
            context={"task": "专利分析"},
        )

        assert feedback_id is not None
        assert len(feedback_system.feedback_history) == 1

        feedback = feedback_system.feedback_history[0]
        assert feedback.satisfaction_level == SatisfactionLevel.VERY_DISSATISFIED
        assert "不准确" in feedback.content

    def test_collect_multiple_feedbacks(self, feedback_system):
        """测试收集多个反馈"""
        satisfactions = [5, 4, 3, 2, 1]
        contents = [
            "优秀",
            "满意",
            "一般",
            "不满意",
            "非常不满意",
        ]

        for sat, content in zip(satisfactions, contents):
            feedback_system.collect_explicit_feedback(sat, content)

        assert len(feedback_system.feedback_history) == 5

        # 验证服务指标已更新
        assert feedback_system.service_metrics.helpfulness > 0


# ========== 隐式反馈测试 ==========

class TestImplicitFeedback:
    """隐式反馈测试"""

    def test_infer_positive_feedback(self, feedback_system):
        """测试推断正面反馈"""
        feedback_id = feedback_system.infer_implicit_feedback(
            user_response="好的，这个方案很棒，谢谢！",
            interaction_context={"task": "方案建议"},
        )

        assert feedback_id is not None
        assert len(feedback_system.feedback_history) == 1

        feedback = feedback_system.feedback_history[0]
        assert feedback.satisfaction_level.value >= 4
        assert feedback.feedback_type == FeedbackType.IMPLICIT

    def test_infer_negative_feedback(self, feedback_system):
        """测试推断负面反馈"""
        feedback_id = feedback_system.infer_implicit_feedback(
            user_response="这个结果不对，很失望",
            interaction_context={"task": "检索"},
        )

        assert feedback_id is not None

        feedback = feedback_system.feedback_history[0]
        assert feedback.satisfaction_level.value <= 2

    def test_infer_neutral_feedback(self, feedback_system):
        """测试推断中性反馈"""
        feedback_id = feedback_system.infer_implicit_feedback(
            user_response="我知道了，收到",  # 使用真正的中性文本
            interaction_context={"task": "信息查询"},
        )

        # 中性反馈不应被记录
        assert feedback_id is None
        assert len(feedback_system.feedback_history) == 0

    def test_sentiment_analysis(self, feedback_system):
        """测试情感分析"""
        # 正面文本
        positive_score = feedback_system._analyze_sentiment("很棒，满意")
        assert positive_score >= 4

        # 负面文本
        negative_score = feedback_system._analyze_sentiment("不好，很差")
        assert negative_score <= 2

        # 中性文本 - 使用真正的中性文本（不含正面/负面关键词）
        neutral_score = feedback_system._analyze_sentiment("我知道了，收到")
        assert neutral_score == 3


# ========== 服务质量评估测试 ==========

class TestServiceQualityEvaluation:
    """服务质量评估测试"""

    def test_evaluate_quality_fast_response(self, feedback_system):
        """测试评估快速响应的质量"""
        response = "这是一个详细的回答，包含了解决方案和示例代码，可以帮助您解决问题。"

        metrics = feedback_system.evaluate_service_quality(
            response=response,
            response_time=2.0,  # 2秒响应
            context={"task": "技术咨询"},
        )

        assert metrics.response_time == 2.0
        assert metrics.accuracy > 0.7
        assert metrics.helpfulness > 0.7
        assert metrics.clarity > 0.7
        assert metrics.completeness > 0.7
        assert metrics.overall_score > 0.7

    def test_evaluate_quality_slow_response(self, feedback_system):
        """测试评估慢速响应的质量"""
        response = "这是一个简单的回答。"

        metrics = feedback_system.evaluate_service_quality(
            response=response,
            response_time=35.0,  # 35秒响应
            context={"task": "查询"},
        )

        # 慢速响应会降低响应时间分数
        time_score = max(0, 1 - metrics.response_time / 30)
        assert time_score < 0.5

    def test_evaluate_accuracy(self, feedback_system):
        """测试准确性评估"""
        # 包含问题关键词的响应
        response = "关于专利检索的问题，这里有几个解决方案..."
        context = {"question": "专利检索"}

        accuracy = feedback_system._evaluate_accuracy(response, context)
        assert accuracy > 0.8

    def test_evaluate_helpfulness(self, feedback_system):
        """测试有用性评估"""
        # 包含有用性指示词的响应
        helpful_response = "建议您尝试以下方法：1. 使用布尔查询 2. 添加同义词扩展"

        helpfulness = feedback_system._evaluate_helpfulness(helpful_response)
        assert helpfulness > 0.7

    def test_evaluate_clarity(self, feedback_system):
        """测试清晰度评估"""
        # 长度适中的响应
        clear_response = "这是第一点。这是第二点，包含详细说明。" * 5

        clarity = feedback_system._evaluate_clarity(clear_response)
        assert clarity > 0.7

    def test_evaluate_completeness(self, feedback_system):
        """测试完整性评估"""
        # 包含示例和解释的响应
        complete_response = "例如，您可以这样使用。因为这样可以提高效率。"

        completeness = feedback_system._evaluate_completeness(complete_response)
        assert completeness > 0.7


# ========== 改进计划测试 ==========

class TestImprovementPlan:
    """改进计划测试"""

    def test_generate_improvement_plan_with_feedback(self, feedback_system):
        """测试基于反馈生成改进计划"""
        # 添加一些反馈
        feedback_system.collect_explicit_feedback(2, "响应太慢了", context={"task": "检索"})
        feedback_system.collect_explicit_feedback(3, "结果还可以，但不够准确")

        plan = feedback_system.generate_improvement_plan()

        assert "current_status" in plan
        assert "problem_areas" in plan
        assert "improvement_actions" in plan
        assert "target_goals" in plan

        # 验证问题识别
        assert plan["current_status"]["avg_satisfaction"] < 4
        assert len(plan["improvement_actions"]) > 0

    def test_generate_improvement_plan_no_feedback(self, feedback_system):
        """测试无反馈时生成改进计划"""
        plan = feedback_system.generate_improvement_plan()

        assert "message" in plan
        assert "暂无足够的反馈数据" in plan["message"]

    def test_identify_problem_areas(self, feedback_system):
        """测试问题领域识别"""
        feedback_system.collect_explicit_feedback(
            1, "响应太慢，等了很久", context={"task": "检索"}
        )

        recent = feedback_system._get_recent_feedback(days=7)
        problem_areas = feedback_system._identify_problem_areas(recent)

        assert problem_areas["response_speed"] > 0


# ========== 数据持久化测试 ==========

class TestDataPersistence:
    """数据持久化测试"""

    def test_save_feedback_data(self, feedback_system, temp_feedback_dir):
        """测试保存反馈数据"""
        feedback_system.collect_explicit_feedback(5, "很好")
        feedback_system._save_feedback_data()

        # 验证文件被创建
        assert os.path.exists(feedback_system.feedback_data_path)
        assert os.path.exists(feedback_system.metrics_data_path)

    def test_load_feedback_data(self, feedback_system, temp_feedback_dir):
        """测试加载反馈数据"""
        # 创建测试数据文件
        test_data = {
            "feedback_history": [
                {
                    "id": "fb_test",
                    "timestamp": datetime.now().isoformat(),
                    "feedback_type": "explicit",
                    "satisfaction_level": 5,
                    "content": "测试反馈",
                    "context": {},
                    "tags": [],
                    "action_taken": None,
                    "impact_score": 0.0,
                }
            ],
            "last_updated": datetime.now().isoformat(),
        }

        with open(feedback_system.feedback_data_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False)

        # 创建新实例并加载数据
        new_system = XiaonuoFeedbackSystem()
        new_system.feedback_data_path = str(temp_feedback_dir / "feedback.json")
        new_system._load_feedback_data()

        assert len(new_system.feedback_history) == 1
        assert new_system.feedback_history[0].content == "测试反馈"


# ========== 反馈摘要测试 ==========

class TestFeedbackSummary:
    """反馈摘要测试"""

    def test_get_feedback_summary_with_data(self, feedback_system):
        """测试获取反馈摘要（有数据）"""
        # 添加多样化的反馈
        for satisfaction in [5, 4, 3, 2, 1]:
            feedback_system.collect_explicit_feedback(satisfaction, f"反馈{satisfaction}")

        summary = feedback_system.get_feedback_summary()

        assert summary["total_feedback"] == 5
        assert "satisfaction_distribution" in summary
        assert "average_satisfaction" in summary
        assert summary["average_satisfaction"] == 3.0

    def test_get_feedback_summary_no_data(self, feedback_system):
        """测试获取反馈摘要（无数据）"""
        summary = feedback_system.get_feedback_summary()

        assert "message" in summary
        assert "暂无反馈数据" in summary["message"]


# ========== 集成测试 ==========

class TestIntegration:
    """集成测试"""

    def test_full_feedback_workflow(self, feedback_system):
        """测试完整的反馈工作流"""
        # 1. 收集明确反馈
        feedback_id1 = feedback_system.collect_explicit_feedback(
            satisfaction=4,
            content="响应很快，结果准确",
            context={"task": "专利检索"},
        )

        # 2. 推断隐式反馈
        feedback_id2 = feedback_system.infer_implicit_feedback(
            user_response="很棒的回答，谢谢！",
            interaction_context={"task": "方案建议"},
        )

        # 3. 评估服务质量
        metrics = feedback_system.evaluate_service_quality(
            response="这是详细的解决方案，包含步骤1、步骤2和示例。",
            response_time=3.5,
            context={"question": "如何优化检索"},
        )

        # 4. 获取反馈摘要
        summary = feedback_system.get_feedback_summary()

        # 5. 生成改进计划
        improvement_plan = feedback_system.generate_improvement_plan()

        # 验证
        assert feedback_id1 is not None
        assert feedback_id2 is not None
        assert metrics.overall_score > 0.7
        assert summary["total_feedback"] >= 2
        assert "current_status" in improvement_plan

    def test_metrics_update_on_feedback(self, feedback_system):
        """测试反馈时更新指标"""
        initial_helpfulness = feedback_system.service_metrics.helpfulness

        # 收集高满意度反馈
        feedback_system.collect_explicit_feedback(5, "很有帮助")

        # 有用性应该增加
        updated_helpfulness = feedback_system.service_metrics.helpfulness
        assert updated_helpfulness >= initial_helpfulness


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
