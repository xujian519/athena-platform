#!/usr/bin/env python3
from __future__ import annotations
"""
小诺评估反馈系统
Xiaonuo Evaluation & Feedback System

用于评估服务质量、收集爸爸反馈并持续改进

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import json
import logging
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""

    EXPLICIT = "explicit"  # 明确反馈
    IMPLICIT = "implicit"  # 隐式反馈
    BEHAVIORAL = "behavioral"  # 行为反馈
    PERFORMANCE = "performance"  # 性能反馈


class SatisfactionLevel(Enum):
    """满意度等级"""

    VERY_SATISFIED = 5
    SATISFIED = 4
    NEUTRAL = 3
    DISSATISFIED = 2
    VERY_DISSATISFIED = 1


@dataclass
class FeedbackItem:
    """反馈项"""

    id: str
    timestamp: datetime
    feedback_type: FeedbackType
    satisfaction_level: SatisfactionLevel
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    action_taken: str | None = None
    impact_score: float = 0.0  # 影响分数


@dataclass
class ServiceMetrics:
    """服务指标"""

    response_time: float  # 响应时间(秒)
    accuracy: float  # 准确性(0-1)
    helpfulness: float  # 有用性(0-1)
    clarity: float  # 清晰度(0-1)
    completeness: float  # 完整性(0-1)
    overall_score: float  # 总体分数


@dataclass
class QualityMetrics:
    """质量指标"""

    consistency_score: float  # 一致性分数
    improvement_rate: float  # 改进率
    error_rate: float  # 错误率
    recovery_time: float  # 恢复时间
    user_retention: float  # 用户留存率


class XiaonuoFeedbackSystem:
    """小诺评估反馈系统"""

    def __init__(self):
        self.name = "小诺评估反馈系统"
        self.version = "v1.0.0"

        # 数据存储
        self.feedback_data_path = "data/feedback/xiaonuo_feedback.json"  # TODO: 确保除数不为零
        self.metrics_data_path = "data/feedback/service_metrics.json"  # TODO: 确保除数不为零

        # 反馈历史
        self.feedback_history: list[FeedbackItem] = []

        # 服务指标
        self.service_metrics = ServiceMetrics(
            response_time=0.0,
            accuracy=0.0,
            helpfulness=0.0,
            clarity=0.0,
            completeness=0.0,
            overall_score=0.0,
        )

        # 质量指标
        self.quality_metrics = QualityMetrics(
            consistency_score=0.0,
            improvement_rate=0.0,
            error_rate=0.0,
            recovery_time=0.0,
            user_retention=0.0,
        )

        # 反馈模式
        self.feedback_patterns = {
            "positive_keywords": ["好", "棒", "满意", "可以", "赞", "厉害", "优秀", "完美"],
            "negative_keywords": ["不好", "差", "不行", "糟糕", "失望", "烦", "错", "问题"],
            "improvement_keywords": ["更好", "改进", "优化", "增强", "提升", "完善"],
        }

        # 加载历史数据
        self._load_feedback_data()

    def _load_feedback_data(self) -> Any:
        """加载反馈数据"""
        try:
            if os.path.exists(self.feedback_data_path):
                with open(self.feedback_data_path, encoding="utf-8") as f:
                    data = json.load(f)
                    feedback_list = data.get("feedback_history", [])
                    self.feedback_history = [
                        FeedbackItem(
                            id=item.get("id"),
                            timestamp=datetime.fromisoformat(item.get("timestamp")),
                            feedback_type=FeedbackType(item.get("feedback_type")),
                            satisfaction_level=SatisfactionLevel(item.get("satisfaction_level")),
                            content=item.get("content"),
                            context=item.get("context", {}),
                            tags=item.get("tags", []),
                            action_taken=item.get("action_taken"),
                            impact_score=item.get("impact_score", 0.0),
                        )
                        for item in feedback_list
                    ]
            print("✅ 成功加载反馈历史")
        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)

    def collect_explicit_feedback(
        self, satisfaction: int, content: str, context: dict[str, Any] | None = None
    ) -> str:
        """收集明确反馈"""
        feedback_id = f"fb_{int(time.time() * 1000)}"

        feedback = FeedbackItem(
            id=feedback_id,
            timestamp=datetime.now(),
            feedback_type=FeedbackType.EXPLICIT,
            satisfaction_level=SatisfactionLevel(satisfaction),
            content=content,
            context=context or {},
            tags=["明确反馈"],
        )

        self.feedback_history.append(feedback)
        self._update_service_metrics(feedback)
        self._save_feedback_data()

        print(f"💭 收集明确反馈: 满意度{satisfaction}/5")
        return feedback_id

    def infer_implicit_feedback(
        self, user_response: str, interaction_context: dict[str, Any]
    ) -> str | None:
        """推断隐式反馈"""
        satisfaction = self._analyze_sentiment(user_response)

        if satisfaction == 3:  # 中性
            return None

        feedback_id = f"fb_{int(time.time() * 1000)}"

        feedback = FeedbackItem(
            id=feedback_id,
            timestamp=datetime.now(),
            feedback_type=FeedbackType.IMPLICIT,
            satisfaction_level=SatisfactionLevel(satisfaction),
            content=f"隐式反馈: {user_response}",
            context=interaction_context,
            tags=["隐式反馈"],
        )

        self.feedback_history.append(feedback)
        self._update_service_metrics(feedback)

        print(f"🤔 推断隐式反馈: 满意度{satisfaction}/5")
        return feedback_id

    def _analyze_sentiment(self, text: str) -> int:
        """分析文本情感"""
        positive_count = sum(
            1 for word in self.feedback_patterns.get("positive_keywords") if word in text
        )
        negative_count = sum(
            1 for word in self.feedback_patterns.get("negative_keywords") if word in text
        )

        if positive_count > negative_count:
            return min(5, 3 + positive_count)
        elif negative_count > positive_count:
            return max(1, 3 - negative_count)
        else:
            return 3

    def evaluate_service_quality(
        self, response: str, response_time: float, context: dict[str, Any] | None = None
    ) -> ServiceMetrics:
        """评估服务质量"""
        # 计算各项指标
        accuracy = self._evaluate_accuracy(response, context)
        helpfulness = self._evaluate_helpfulness(response, context)
        clarity = self._evaluate_clarity(response)
        completeness = self._evaluate_completeness(response, context)

        # 计算总体分数
        weights = [0.25, 0.25, 0.2, 0.2, 0.1]  # 响应时间、准确性、有用性、清晰度、完整性
        scores = [
            max(0, 1 - response_time / 30),  # 30秒内为满分
            accuracy,
            helpfulness,
            clarity,
            completeness,
        ]

        overall_score = sum(w * s for w, s in zip(weights, scores, strict=False))

        # 更新服务指标
        self.service_metrics = ServiceMetrics(
            response_time=response_time,
            accuracy=accuracy,
            helpfulness=helpfulness,
            clarity=clarity,
            completeness=completeness,
            overall_score=overall_score,
        )

        return self.service_metrics

    def _evaluate_accuracy(self, response: str, context: dict[str, Any] | None = None) -> float:
        """评估准确性"""
        # 简化的准确性评估
        if not context:
            return 0.8  # 默认值

        # 检查是否回答了问题
        if "question" in context:
            question = context["question"]
            if any(keyword in response for keyword in question.split() if len(keyword) > 2):
                return 0.9

        return 0.8

    def _evaluate_helpfulness(self, response: str, context: dict[str, Any] | None = None) -> float:
        """评估有用性"""
        helpfulness_indicators = [
            "建议",
            "方案",
            "解决",
            "方法",
            "步骤",
            "示例",
            "参考",
            "可以尝试",
        ]

        helpful_count = sum(1 for indicator in helpfulness_indicators if indicator in response)
        return min(1.0, 0.6 + helpful_count * 0.1)

    def _evaluate_clarity(self, response: str) -> float:
        """评估清晰度"""
        # 基于长度和结构的简化评估
        if 50 <= len(response) <= 500:
            length_score = 1.0
        elif len(response) < 50:
            length_score = 0.7
        else:
            length_score = 0.8

        # 检查结构
        structure_score = 0.8
        if "," in response and "。" in response:
            structure_score = 1.0

        return (length_score + structure_score) / 2

    def _evaluate_completeness(self, response: str, context: dict[str, Any] | None = None) -> float:
        """评估完整性"""
        completeness_score = 0.8  # 基础分数

        # 检查是否包含示例
        if "例如" in response or "比如" in response:
            completeness_score += 0.1

        # 检查是否包含解释
        if "因为" in response or "由于" in response:
            completeness_score += 0.1

        return min(1.0, completeness_score)

    def generate_improvement_plan(self) -> dict[str, Any]:
        """生成改进计划"""
        # 分析最近的反馈
        recent_feedback = self._get_recent_feedback(days=7)

        if not recent_feedback:
            return {"message": "暂无足够的反馈数据生成改进计划"}

        # 计算平均满意度
        avg_satisfaction = statistics.mean([f.satisfaction_level.value for f in recent_feedback])

        # 识别问题领域
        problem_areas = self._identify_problem_areas(recent_feedback)

        # 生成改进建议
        improvements = []

        if avg_satisfaction < 3.5:
            improvements.append("整体满意度偏低,需要全面提升服务质量")

        if problem_areas.get("response_speed", 0) > 0.3:
            improvements.append("响应速度需要优化,目标:减少到5秒以内")

        if problem_areas.get("accuracy", 0) > 0.3:
            improvements.append("准确性需要提升,增加事实核查机制")

        if problem_areas.get("helpfulness", 0) > 0.3:
            improvements.append("有用性需要增强,提供更多实用建议")

        # 设置改进目标
        goals = {
            "satisfaction_target": min(5.0, avg_satisfaction + 0.5),
            "response_time_target": 5.0,
            "accuracy_target": 0.9,
            "helpfulness_target": 0.85,
        }

        return {
            "current_status": {
                "avg_satisfaction": avg_satisfaction,
                "total_feedback": len(recent_feedback),
                "service_metrics": asdict(self.service_metrics),
            },
            "problem_areas": problem_areas,
            "improvement_actions": improvements,
            "target_goals": goals,
            "timeline": "2周内见效,1个月内达标",
        }

    def _get_recent_feedback(self, days: int = 7) -> list[FeedbackItem]:
        """获取最近的反馈"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [f for f in self.feedback_history if f.timestamp > cutoff_date]

    def _identify_problem_areas(self, feedback_list: list[FeedbackItem]) -> dict[str, float]:
        """识别问题领域"""
        problem_areas = {
            "response_speed": 0.0,
            "accuracy": 0.0,
            "helpfulness": 0.0,
            "clarity": 0.0,
            "completeness": 0.0,
        }

        # 分析反馈内容中的问题
        for feedback in feedback_list:
            content = feedback.content.lower()
            satisfaction = feedback.satisfaction_level.value

            if satisfaction <= 2:  # 不满意
                if "慢" in content or "时间" in content:
                    problem_areas["response_speed"] += 0.1
                if "错" in content or "不准确" in content:
                    problem_areas["accuracy"] += 0.1
                if "没用" in content or "没帮助" in content:
                    problem_areas["helpfulness"] += 0.1
                if "不清楚" in content or "难懂" in content:
                    problem_areas["clarity"] += 0.1
                if "不完整" in content or "缺少" in content:
                    problem_areas["completeness"] += 0.1

        return problem_areas

    def _update_service_metrics(self, feedback: FeedbackItem) -> Any:
        """更新服务指标"""
        # 基于满意度更新指标
        satisfaction_value = feedback.satisfaction_level.value / 5.0

        # 使用指数移动平均更新
        alpha = 0.1  # 学习率

        self.service_metrics.helpfulness = (
            self.service_metrics.helpfulness * (1 - alpha) + satisfaction_value * alpha
        )

        # 更新质量指标
        self._update_quality_metrics()

    def _update_quality_metrics(self) -> Any:
        """更新质量指标"""
        recent_feedback = self._get_recent_feedback(days=30)

        if len(recent_feedback) < 2:
            return

        # 计算改进率
        recent_half = recent_feedback[len(recent_feedback) // 2 :]
        early_half = recent_feedback[: len(recent_feedback) // 2]

        recent_avg = statistics.mean([f.satisfaction_level.value for f in recent_half])
        early_avg = statistics.mean([f.satisfaction_level.value for f in early_half])

        self.quality_metrics.improvement_rate = (recent_avg - early_avg) / early_avg

        # 计算错误率
        errors = sum(1 for f in recent_feedback if f.satisfaction_level.value <= 2)
        self.quality_metrics.error_rate = errors / len(recent_feedback)

        # 计算一致性(满意度方差)
        satisfaction_values = [f.satisfaction_level.value for f in recent_feedback]
        if len(satisfaction_values) > 1:
            variance = statistics.variance(satisfaction_values)
            self.quality_metrics.consistency_score = max(0, 1 - variance / 4)

    def _save_feedback_data(self) -> Any:
        """保存反馈数据"""
        try:
            os.makedirs(os.path.dirname(self.feedback_data_path), exist_ok=True)

            # 保存反馈历史
            feedback_data = {
                "feedback_history": [
                    {
                        "id": f.id,
                        "timestamp": f.timestamp.isoformat(),
                        "feedback_type": f.feedback_type.value,
                        "satisfaction_level": f.satisfaction_level.value,
                        "content": f.content,
                        "context": f.context,
                        "tags": f.tags,
                        "action_taken": f.action_taken,
                        "impact_score": f.impact_score,
                    }
                    for f in self.feedback_history
                ],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.feedback_data_path, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)

            # 保存服务指标
            metrics_data = {
                "service_metrics": asdict(self.service_metrics),
                "quality_metrics": asdict(self.quality_metrics),
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.metrics_data_path, "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)

    def get_feedback_summary(self) -> dict[str, Any]:
        """获取反馈摘要"""
        if not self.feedback_history:
            return {"message": "暂无反馈数据"}

        # 统计信息
        total_feedback = len(self.feedback_history)
        recent_feedback = self._get_recent_feedback(days=30)

        # 满意度分布
        satisfaction_counts = {}
        for level in SatisfactionLevel:
            count = sum(1 for f in self.feedback_history if f.satisfaction_level == level)
            satisfaction_counts[level.name] = count

        # 平均满意度
        avg_satisfaction = statistics.mean(
            [f.satisfaction_level.value for f in self.feedback_history]
        )

        # 反馈类型分布
        type_counts = {}
        for ftype in FeedbackType:
            count = sum(1 for f in self.feedback_history if f.feedback_type == ftype)
            type_counts[ftype.value] = count

        return {
            "total_feedback": total_feedback,
            "recent_feedback_30d": len(recent_feedback),
            "satisfaction_distribution": satisfaction_counts,
            "average_satisfaction": avg_satisfaction,
            "feedback_type_distribution": type_counts,
            "service_metrics": asdict(self.service_metrics),
            "quality_metrics": asdict(self.quality_metrics),
            "trend": "improving" if self.quality_metrics.improvement_rate > 0 else "stable",
        }


# 导出主类
__all__ = [
    "FeedbackItem",
    "QualityMetrics",
    "ServiceMetrics",
    "XiaonuoFeedbackSystem",
    # 别名
    "FeedbackCollector",  # 别名
    "FeedbackProcessor",  # 别名
]


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 FeedbackCollector 作为别名
FeedbackCollector = XiaonuoFeedbackSystem

# 为保持兼容性，提供 FeedbackProcessor 作为别名
FeedbackProcessor = XiaonuoFeedbackSystem
