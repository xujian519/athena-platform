#!/usr/bin/env python3
"""
小诺工具效果反馈循环系统
Xiaonuo Tool Effect Feedback Loop System

建立工具执行效果评估、用户满意度收集、效果-选择关联学习和自适应优化机制

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "智能反馈循环95%+"
"""

from __future__ import annotations
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

from core.logging_config import setup_logging

# 安全序列化和模型加载
try:
    import joblib

except ImportError:

    def serialize_for_cache(obj: Any) -> bytes:
        return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")

    def deserialize_from_cache(data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))


import jieba
from sklearn.ensemble import RandomForestClassifier

# 机器学习库
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class FeedbackType(Enum):
    """反馈类型"""

    EXECUTION_SUCCESS = "execution_success"  # 执行成功
    EXECUTION_FAILURE = "execution_failure"  # 执行失败
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度
    PERFORMANCE_METRICS = "performance_metrics"  # 性能指标
    CONTEXT_RELEVANCE = "context_relevance"  # 上下文相关性
    QUALITY_ASSESSMENT = "quality_assessment"  # 质量评估
    AUTOMATIC_DETECTION = "automatic_detection"  # 自动检测
    EXPLICIT_FEEDBACK = "explicit_feedback"  # 明确反馈


class FeedbackChannel(Enum):
    """反馈渠道"""

    AUTOMATIC_DETECTION = "automatic_detection"  # 自动检测
    USER_EXPLICIT = "user_explicit"  # 用户明确反馈
    IMPLICIT_MONITORING = "implicit_monitoring"  # 隐式监控
    SURVEY_COLLECTION = "survey_collection"  # 问卷调查


@dataclass
class FeedbackRecord:
    """反馈记录"""

    timestamp: datetime
    user_id: str
    tool_name: str
    intent: str
    context: dict[str, Any]
    feedback_type: FeedbackType
    feedback_channel: FeedbackChannel
    execution_success: bool
    response_time: float
    satisfaction_score: float  # 0-1
    quality_metrics: dict[str, float] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    user_comments: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolPerformanceMetrics:
    """工具性能指标"""

    tool_name: str
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    avg_satisfaction: float = 0.0
    success_rate: float = 0.0
    quality_score: float = 0.0
    reliability_score: float = 0.0
    efficiency_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackLoopConfig:
    """反馈循环配置"""

    # 学习参数
    learning_rate: float = 0.1
    decay_factor: float = 0.95
    min_feedback_threshold: int = 10
    confidence_threshold: float = 0.8

    # 反馈权重
    execution_weight: float = 0.4
    satisfaction_weight: float = 0.3
    performance_weight: float = 0.2
    quality_weight: float = 0.1

    # 优化参数
    optimization_cycle_hours: int = 24
    auto_optimization_enabled: bool = True
    feedback_retention_days: int = 90

    # 路径配置
    model_dir: str = "models/feedback_loop"
    data_dir: str = "data/feedback_loop"


class XiaonuoFeedbackLoop:
    """小诺工具效果反馈循环系统 - 🔧 线程安全修复:添加线程锁保护"""

    def __init__(self, config: FeedbackLoopConfig | None = None):
        self.config = config if config is not None else FeedbackLoopConfig()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # 反馈数据存储
        self.feedback_records: list[FeedbackRecord] = []
        self.tool_metrics: dict[str, ToolPerformanceMetrics] = {}
        # 用户反馈模式: user_id -> tool_name -> metrics_dict
        self.user_feedback_patterns: dict[str, dict[str, dict[str, float]]] = {}

        # 机器学习模型
        self.feedback_predictor = None
        self.feature_vectorizer = None
        self.feature_scaler = None

        # 优化相关
        self.optimization_history: list[dict[str, Any]] = []

        # 🔧 线程安全修复:添加线程锁
        import threading

        self._lock = threading.RLock()

        # 初始化
        self._init_jieba()

        logger.info("🔄 小诺工具效果反馈循环系统初始化完成")
        logger.info(f"📊 反馈类型数量: {len(FeedbackType)}")
        logger.info(f"📋 反馈渠道数量: {len(FeedbackChannel)}")

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        # 添加反馈相关词汇
        feedback_words = [
            "反馈",
            "评价",
            "满意度",
            "成功",
            "失败",
            "效果",
            "质量",
            "性能",
            "响应时间",
            "可靠性",
            "效率",
            "改进",
            "优化",
            "调整",
            "学习",
            "适应",
        ]

        for word in feedback_words:
            jieba.add_word(word, freq=1000)

    def record_feedback(
        self,
        user_id: str,
        tool_name: str,
        intent: str,
        context: dict[str, Any],        feedback_type: FeedbackType,
        feedback_channel: FeedbackChannel,
        execution_success: bool,
        response_time: float,
        satisfaction_score: float | None = None,
        quality_metrics: dict[str, float] | None = None,
        performance_metrics: dict[str, float] | None = None,
        user_comments: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        """记录反馈 - 🔧 线程安全修复:添加线程锁保护"""
        feedback = FeedbackRecord(
            timestamp=datetime.now(),
            user_id=user_id,
            tool_name=tool_name,
            intent=intent,
            context=context,
            feedback_type=feedback_type,
            feedback_channel=feedback_channel,
            execution_success=execution_success,
            response_time=response_time,
            satisfaction_score=satisfaction_score or (1.0 if execution_success else 0.0),
            quality_metrics=quality_metrics or {},
            performance_metrics=performance_metrics or {},
            user_comments=user_comments,
            metadata=metadata or {},
        )

        # 线程安全修复:使用锁保护反馈记录
        with self._lock:
            self.feedback_records.append(feedback)

            # 更新工具指标
            self._update_tool_metrics(tool_name, feedback)

            # 更新用户反馈模式
            self._update_user_feedback_patterns(user_id, tool_name, feedback)

        # 触发即时优化检查(在锁外执行,避免死锁)
        self._check_optimization_trigger(tool_name)

        logger.info(f"📝 记录反馈: {user_id} - {tool_name} - {feedback_type.value}")

    def _update_tool_metrics(self, tool_name: str, feedback: FeedbackRecord) -> Any:
        """更新工具性能指标"""
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolPerformanceMetrics(tool_name=tool_name)

        metrics = self.tool_metrics[tool_name]
        metrics.total_executions += 1

        if feedback.execution_success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1

        # 更新响应时间
        metrics.avg_response_time = (
            metrics.avg_response_time * (metrics.total_executions - 1) + feedback.response_time
        ) / metrics.total_executions

        # 更新满意度(satisfaction_score始终为float类型)
        metrics.avg_satisfaction = (
            metrics.avg_satisfaction * (metrics.total_executions - 1) + feedback.satisfaction_score
        ) / metrics.total_executions

        # 计算综合指标
        metrics.success_rate = metrics.success_count / metrics.total_executions
        metrics.reliability_score = self._calculate_reliability_score(metrics)
        metrics.efficiency_score = self._calculate_efficiency_score(metrics)
        metrics.quality_score = self._calculate_quality_score(metrics, feedback)

        metrics.last_updated = datetime.now()

    def _calculate_reliability_score(self, metrics: ToolPerformanceMetrics) -> float:
        """计算可靠性分数"""
        # 基于成功率和失败模式
        base_reliability = metrics.success_rate

        # 考虑失败模式的严重性
        if metrics.total_executions >= 10:
            # 检查最近的成功率趋势
            recent_feedbacks = [
                f
                for f in self.feedback_records[-20:]
                if f.tool_name == metrics.tool_name
                and f.timestamp >= datetime.now() - timedelta(days=7)
            ]

            if recent_feedbacks:
                recent_success_rate = sum(1 for f in recent_feedbacks if f.execution_success) / len(
                    recent_feedbacks
                )
                # 如果最近成功率更高,给予奖励
                if recent_success_rate > metrics.success_rate:
                    base_reliability += 0.1

        return min(base_reliability, 1.0)

    def _calculate_efficiency_score(self, metrics: ToolPerformanceMetrics) -> float:
        """计算效率分数"""
        # 基于响应时间和成功率
        time_factor = max(0, 1.0 - metrics.avg_response_time / 10.0)  # 10秒为基准
        success_factor = metrics.success_rate

        return time_factor * 0.4 + success_factor * 0.6

    def _calculate_quality_score(
        self, metrics: ToolPerformanceMetrics, feedback: FeedbackRecord
    ) -> float:
        """计算质量分数"""
        base_quality = 0.5

        # 基于执行结果
        if feedback.execution_success:
            base_quality += 0.3

        # 基于满意度
        if feedback.satisfaction_score:
            base_quality = base_quality * 0.7 + feedback.satisfaction_score * 0.3

        # 基于质量指标
        if feedback.quality_metrics:
            avg_quality = float(np.mean(list(feedback.quality_metrics.values())))
            base_quality = base_quality * 0.8 + avg_quality * 0.2

        return float(min(base_quality, 1.0))

    def _update_user_feedback_patterns(
        self, user_id: str, tool_name: str, feedback: FeedbackRecord
    ) -> Any:
        """更新用户反馈模式"""
        if user_id not in self.user_feedback_patterns:
            self.user_feedback_patterns[user_id] = {}

        # 获取或创建工具模式
        if tool_name not in self.user_feedback_patterns[user_id]:
            self.user_feedback_patterns[user_id][tool_name] = {}

        tool_pattern = self.user_feedback_patterns[user_id][tool_name]
        assert isinstance(tool_pattern, dict), "tool_pattern should be a dict"

        # 基于不同反馈类型更新模式
        if feedback.feedback_type == FeedbackType.EXECUTION_SUCCESS:
            current_rate = tool_pattern.get("execution_success_rate", 0.5)
            tool_pattern["execution_success_rate"] = current_rate * 0.9 + 1.0 * 0.1
        elif feedback.feedback_type == FeedbackType.USER_SATISFACTION:
            current_trend = tool_pattern.get("satisfaction_trend", 0.5)
            tool_pattern["satisfaction_trend"] = (
                current_trend * 0.9 + feedback.satisfaction_score * 0.1
            )

    def _check_optimization_trigger(self, tool_name: str) -> Any:
        """检查优化触发条件"""
        if not self.config.auto_optimization_enabled:
            return

        metrics = self.tool_metrics.get(tool_name)
        if not metrics or metrics.total_executions < self.config.min_feedback_threshold:
            return

        # 检查是否需要优化
        needs_optimization = False
        optimization_reasons = []

        # 成功率过低
        if metrics.success_rate < 0.7:
            needs_optimization = True
            optimization_reasons.append(f"成功率过低: {metrics.success_rate:.2f}")

        # 满意度过低
        if metrics.avg_satisfaction < 0.6:
            needs_optimization = True
            optimization_reasons.append(f"满意度过低: {metrics.avg_satisfaction:.2f}")

        # 响应时间过长
        if metrics.avg_response_time > 5.0:
            needs_optimization = True
            optimization_reasons.append(f"响应时间过长: {metrics.avg_response_time:.2f}s")

        # 质量分数过低
        if metrics.quality_score < 0.6:
            needs_optimization = True
            optimization_reasons.append(f"质量分数过低: {metrics.quality_score:.2f}")

        if needs_optimization:
            self._trigger_optimization(tool_name, optimization_reasons)

    def _trigger_optimization(self, tool_name: str, reasons: list[str]) -> Any:
        """触发优化"""
        logger.info(f"🔧 触发工具优化: {tool_name}")
        for reason in reasons:
            logger.info(f"  - {reason}")

        optimization_record = {
            "timestamp": datetime.now(),
            "tool_name": tool_name,
            "reasons": reasons,
            "metrics_before": self.tool_metrics[tool_name].__dict__.copy(),
            "optimization_action": "triggered",
        }

        self.optimization_history.append(optimization_record)

        # 执行优化逻辑
        self._execute_optimization(tool_name)

    def _execute_optimization(self, tool_name: str) -> Any:
        """执行优化逻辑"""
        metrics = self.tool_metrics[tool_name]

        # 分析问题并提出优化建议
        optimization_suggestions = []

        if metrics.success_rate < 0.7:
            optimization_suggestions.append("提高工具可靠性:增加错误处理和重试机制")
            optimization_suggestions.append("改进参数验证逻辑,确保输入正确")

        if metrics.avg_satisfaction < 0.6:
            optimization_suggestions.append("优化用户体验:改进响应质量和相关性")
            optimization_suggestions.append("增加个性化配置选项")

        if metrics.avg_response_time > 5.0:
            optimization_suggestions.append("优化性能:实现缓存和预处理")
            optimization_suggestions.append("考虑并行处理或异步操作")

        # 记录优化建议
        if optimization_suggestions:
            logger.info(f"💡 优化建议 for {tool_name}:")
            for i, suggestion in enumerate(optimization_suggestions, 1):
                logger.info(f"  {i}. {suggestion}")

            # 更新优化记录
            if self.optimization_history:
                self.optimization_history[-1]["optimization_suggestions"] = optimization_suggestions
                self.optimization_history[-1]["optimization_action"] = "completed"

    def analyze_feedback_patterns(
        self, tool_name: str | None = None, days: int = 30
    ) -> dict[str, Any]:
        """分析反馈模式"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # 筛选反馈记录
        filtered_feedback = [
            f
            for f in self.feedback_records
            if f.timestamp >= cutoff_date and (tool_name is None or f.tool_name == tool_name)
        ]

        if not filtered_feedback:
            return {"error": "没有反馈数据"}

        # 初始化统计数据结构
        feedback_by_type: dict[str, int] = {}
        feedback_by_channel: dict[str, int] = {}
        user_patterns: dict[str, dict[str, Any]] = {}
        tool_performance: dict[str, dict[str, Any]] = {}

        # 计算基础指标
        success_rate = sum(1 for f in filtered_feedback if f.execution_success) / len(
            filtered_feedback
        )
        avg_satisfaction = float(np.mean([f.satisfaction_score for f in filtered_feedback]))
        avg_response_time = float(np.mean([f.response_time for f in filtered_feedback]))

        analysis = {
            "period_days": days,
            "total_feedbacks": len(filtered_feedback),
            "feedback_by_type": feedback_by_type,
            "feedback_by_channel": feedback_by_channel,
            "success_rate": success_rate,
            "avg_satisfaction": avg_satisfaction,
            "avg_response_time": avg_response_time,
            "user_patterns": user_patterns,
            "tool_performance": tool_performance,
        }

        # 统计反馈类型和渠道
        for feedback in filtered_feedback:
            fb_type = feedback.feedback_type.value
            feedback_by_type[fb_type] = feedback_by_type.get(fb_type, 0) + 1

            fb_channel = feedback.feedback_channel.value
            feedback_by_channel[fb_channel] = feedback_by_channel.get(fb_channel, 0) + 1

        # 用户模式分析
        user_feedbacks: dict[str, list[FeedbackRecord]] = {}
        for feedback in filtered_feedback:
            if feedback.user_id not in user_feedbacks:
                user_feedbacks[feedback.user_id] = []
            user_feedbacks[feedback.user_id].append(feedback)

        for user_id, user_feedback_list in user_feedbacks.items():
            user_success_rate = sum(1 for f in user_feedback_list if f.execution_success) / len(
                user_feedback_list
            )
            user_satisfaction = float(np.mean([f.satisfaction_score for f in user_feedback_list]))
            # 修复lambda类型
            tool_counts: dict[str, int] = {}
            for f in user_feedback_list:
                tool_counts[f.tool_name] = tool_counts.get(f.tool_name, 0) + 1
            user_favorite_tool = max(tool_counts.keys(), key=lambda x: tool_counts[x])

            user_patterns[user_id] = {
                "total_feedbacks": len(user_feedback_list),
                "success_rate": user_success_rate,
                "avg_satisfaction": user_satisfaction,
                "favorite_tool": user_favorite_tool,
            }

        # 工具性能分析
        if not tool_name:
            # 分析所有工具
            tool_feedbacks: dict[str, list[FeedbackRecord]] = {}
            for feedback in filtered_feedback:
                if feedback.tool_name not in tool_feedbacks:
                    tool_feedbacks[feedback.tool_name] = []
                tool_feedbacks[feedback.tool_name].append(feedback)

            for tool, feedbacks in tool_feedbacks.items():
                if tool in self.tool_metrics:
                    tool_performance[tool] = {
                        "metrics": self.tool_metrics[tool].__dict__.copy(),
                        "feedback_count": len(feedbacks),
                        "avg_satisfaction": float(
                            np.mean([f.satisfaction_score for f in feedbacks])
                        ),
                        "recent_trend": self._calculate_recent_trend(feedbacks),
                    }
        else:
            # 分析特定工具
            if tool_name in self.tool_metrics:
                tool_filtered = [f for f in filtered_feedback if f.tool_name == tool_name]
                tool_performance[tool_name] = {
                    "metrics": self.tool_metrics[tool_name].__dict__.copy(),
                    "feedback_count": len(tool_filtered),
                    "avg_satisfaction": float(
                        np.mean([f.satisfaction_score for f in tool_filtered])
                    ),
                    "recent_trend": self._calculate_recent_trend(tool_filtered),
                }

        return analysis

    def _calculate_recent_trend(self, feedbacks: list[FeedbackRecord]) -> str:
        """计算最近趋势"""
        if len(feedbacks) < 3:
            return "insufficient_data"

        # 计算最近几次的满意度趋势
        recent_satisfaction = [f.satisfaction_score for f in feedbacks[-5:]]

        if len(recent_satisfaction) >= 3:
            trend = np.polyfit(range(len(recent_satisfaction)), recent_satisfaction, 1)[0]

            if trend > 0.05:
                return "improving"
            elif trend < -0.05:
                return "declining"
            else:
                return "stable"

        return "unclear"

    def train_feedback_predictor(self) -> Any:
        """训练反馈预测模型"""
        logger.info("🚀 开始训练反馈预测模型...")

        if len(self.feedback_records) < 50:
            logger.warning("⚠️ 反馈数据不足,无法训练模型")
            return

        # 准备训练数据
        training_data = []
        labels = []

        for feedback in self.feedback_records:
            features = self._extract_feedback_features(feedback)
            training_data.append(features)

            # 标签:是否需要优化
            metrics = self.tool_metrics.get(feedback.tool_name)
            needs_optimization = (
                not feedback.execution_success
                or (metrics and metrics.success_rate < 0.8)
                or feedback.satisfaction_score < 0.7
            )
            labels.append(1 if needs_optimization else 0)

        if len(training_data) == 0:
            logger.warning("⚠️ 没有有效的训练特征")
            return

        X = np.array(training_data)
        y = np.array(labels)

        # 特征缩放(所有特征都是数值型的)
        self.feature_scaler = StandardScaler()
        X_scaled = self.feature_scaler.fit_transform(X)

        # 训练模型
        self.feedback_predictor = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )

        self.feedback_predictor.fit(X_scaled, y)

        # 评估模型
        y_pred = self.feedback_predictor.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)

        logger.info("✅ 反馈预测模型训练完成")
        logger.info(f"📊 模型准确率: {accuracy:.4f}")

        return accuracy

    def _extract_feedback_features(self, feedback: FeedbackRecord) -> list[float]:
        """提取反馈特征"""
        features = []

        # 时间特征
        features.append(feedback.timestamp.hour / 24.0)  # 小时
        features.append(feedback.timestamp.weekday() / 7.0)  # 星期

        # 响应时间特征
        features.append(min(feedback.response_time / 10.0, 1.0))  # 响应时间(归一化)

        # 执行结果特征
        features.append(1.0 if feedback.execution_success else 0.0)  # 执行成功

        # 满意度特征
        features.append(feedback.satisfaction_score)

        # 质量指标特征
        if feedback.quality_metrics:
            features.append(np.mean(list(feedback.quality_metrics.values())))
            features.append(len(feedback.quality_metrics))
        else:
            features.append(0.5)  # 默认质量分数
            features.append(0)  # 质量指标数量

        # 性能指标特征
        if feedback.performance_metrics:
            features.append(np.mean(list(feedback.performance_metrics.values())))
            features.append(len(feedback.performance_metrics))
        else:
            features.append(0.5)  # 默认性能分数
            features.append(0)  # 性能指标数量

        # 文本特征(用于向量化)
        text_features = f"{feedback.intent} {feedback.user_comments}"
        features.append(len(text_features.split()))  # 文本长度

        # 用户历史特征
        user_feedbacks = [f for f in self.feedback_records if f.user_id == feedback.user_id]
        if user_feedbacks:
            user_success_rate = sum(1 for f in user_feedbacks if f.execution_success) / len(
                user_feedbacks
            )
            features.append(user_success_rate)
            features.append(len(user_feedbacks))
        else:
            features.append(0.5)
            features.append(0)

        # 工具历史特征
        tool_feedbacks = [f for f in self.feedback_records if f.tool_name == feedback.tool_name]
        if tool_feedbacks:
            tool_success_rate = sum(1 for f in tool_feedbacks if f.execution_success) / len(
                tool_feedbacks
            )
            features.append(tool_success_rate)
            features.append(len(tool_feedbacks))
        else:
            features.append(0.5)
            features.append(0)

        return features

    def predict_optimization_need(
        self, tool_name: str, user_id: str, intent: str, context: dict[str, Any] | None = None
    ) -> tuple[float, str]:
        """预测优化需求"""
        if not self.feedback_predictor:
            return 0.5, "模型未训练"

        # 模拟反馈记录
        mock_feedback = FeedbackRecord(
            timestamp=datetime.now(),
            user_id=user_id,
            tool_name=tool_name,
            intent=intent,
            context=context or {},
            feedback_type=FeedbackType.AUTOMATIC_DETECTION,
            feedback_channel=FeedbackChannel.AUTOMATIC_DETECTION,
            execution_success=True,  # 默认假设成功
            response_time=2.0,  # 默认响应时间
            satisfaction_score=0.7,  # 默认满意度
        )

        features = self._extract_feedback_features(mock_feedback)
        X = np.array([features])

        # 应用特征转换
        if self.feature_vectorizer and self.feature_scaler:
            X_text = self.feature_vectorizer.transform([features[5]])
            X_combined = np.hstack([X[:, :-1], X_text.toarray()])
            X_scaled = self.feature_scaler.transform(X_combined)
        else:
            X_scaled = X

        # 预测(处理单类情况)
        probabilities = self.feedback_predictor.predict_proba(X_scaled)[0]
        if len(probabilities) == 1:
            optimization_prob = 0.0  # 如果只有一个类别,默认为不需要优化
        else:
            optimization_prob = probabilities[1]  # 需要优化的概率

        explanation = self._generate_optimization_explanation(
            optimization_prob, mock_feedback, tool_name
        )

        return optimization_prob, explanation

    def _generate_optimization_explanation(
        self, prob: float, feedback: FeedbackRecord, tool_name: str
    ) -> str:
        """生成优化解释"""
        if prob > 0.8:
            return f"基于历史反馈,{tool_name}很可能需要优化"

        reasons = []

        if feedback.response_time > 5.0:
            reasons.append("响应时间较长")
        if feedback.satisfaction_score < 0.6:
            reasons.append("预期满意度较低")
        if not feedback.execution_success:
            reasons.append("预期执行失败")

        # 检查历史指标
        metrics = self.tool_metrics.get(tool_name)
        if metrics:
            if metrics.success_rate < 0.8:
                reasons.append(f"历史成功率较低({metrics.success_rate:.2f})")
            if metrics.avg_satisfaction < 0.7:
                reasons.append(f"历史满意度较低({metrics.avg_satisfaction:.2f})")

        if reasons:
            return f"需要优化: {', '.join(reasons)}"
        else:
            return "目前表现良好,无需优化"

    def save_models(self) -> None:
        """保存模型 - 🔧 安全修复:使用上下文管理器和线程锁"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"feedback_loop_models_{timestamp}.pkl")

        # 线程安全修复:使用锁保护数据读取
        with self._lock:
            model_data = {
                "feedback_records": self.feedback_records,
                "tool_metrics": self.tool_metrics,
                "user_feedback_patterns": dict(self.user_feedback_patterns),
                "optimization_history": self.optimization_history,
                "feedback_predictor": self.feedback_predictor,
                "feature_vectorizer": self.feature_vectorizer,
                "feature_scaler": self.feature_scaler,
                "config": self.config,
            }

        # 安全修复:使用上下文管理器确保文件正确关闭
        with open(model_path, "wb") as f:
            import joblib

            joblib.dump(model_data, f)

        # 保存最新模型
        latest_path = os.path.join(self.config.model_dir, "latest_feedback_loop_models.pkl")
        with open(latest_path, "wb") as f:
            import joblib

            joblib.dump(model_data, f)

        logger.info(f"💾 反馈循环模型已保存: {model_path}")

    def load_models(self, model_path: str | None = None) -> Any | None:
        """加载模型 - 🔧 安全修复:使用上下文管理器和线程锁"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_feedback_loop_models.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 安全修复:使用上下文管理器确保文件正确关闭
        with open(model_path, "rb") as f:
            import joblib

            model_data = joblib.load(f)

        # 线程安全修复:使用锁保护数据更新
        with self._lock:
            self.feedback_records = model_data["feedback_records"]
            self.tool_metrics = model_data["tool_metrics"]
            self.user_feedback_patterns = defaultdict(dict, model_data["user_feedback_patterns"])
            self.optimization_history = model_data["optimization_history"]
            self.feedback_predictor = model_data.get("feedback_predictor")
            self.feature_vectorizer = model_data.get("feature_vectorizer")
            self.feature_scaler = model_data.get("feature_scaler")
            self.config = model_data["config"]

        logger.info(f"✅ 反馈循环模型已加载: {model_path}")


def main() -> None:
    """主函数"""
    logger.info("🔄 小诺工具效果反馈循环系统测试开始")

    # 创建配置
    config = FeedbackLoopConfig()

    # 创建反馈循环系统
    feedback_loop = XiaonuoFeedbackLoop(config)

    # 模拟反馈数据
    try:
        user_id = "dad"

        # 模拟多次反馈 - 使用类型化的数据结构
        from typing import TypedDict

        class FeedbackDataEntry(TypedDict):
            tool: str
            intent: str
            context: dict[str, Any]
            success: bool
            response_time: float
            satisfaction: float
            comments: str

        feedback_data: list[FeedbackDataEntry] = [
            # 成功的代码分析
            {
                "tool": "code_analyzer",
                "intent": "technical",
                "context": {"urgency": 0.7},
                "success": True,
                "response_time": 2.1,
                "satisfaction": 0.9,
                "comments": "代码分析结果很准确",
            },
            # 失败的API测试
            {
                "tool": "api_tester",
                "intent": "technical",
                "context": {"urgency": 0.9},
                "success": False,
                "response_time": 8.5,
                "satisfaction": 0.3,
                "comments": "接口测试失败,超时了",
            },
            # 满意的聊天交流
            {
                "tool": "chat_companion",
                "intent": "emotional",
                "context": {"time_sensitive": 0.2},
                "success": True,
                "response_time": 1.2,
                "satisfaction": 0.95,
                "comments": "聊天很贴心,回应很及时",
            },
            # 一般的网络搜索
            {
                "tool": "web_search",
                "intent": "query",
                "context": {"resource_limited": 0.5},
                "success": True,
                "response_time": 3.8,
                "satisfaction": 0.7,
                "comments": "搜索结果还可以",
            },
        ]

        # 记录反馈
        for data in feedback_data:
            feedback_loop.record_feedback(
                user_id=user_id,
                tool_name=data["tool"],
                intent=data["intent"],
                context=data["context"],
                feedback_type=FeedbackType.USER_SATISFACTION,
                feedback_channel=FeedbackChannel.USER_EXPLICIT,
                execution_success=data["success"],
                response_time=data["response_time"],
                satisfaction_score=data["satisfaction"],
                user_comments=data["comments"],
            )

        # 训练预测模型
        # 先添加更多模拟数据以满足训练需求
        for i in range(50):
            mock_success = i % 3 != 0  # 2/3成功率
            mock_satisfaction = 0.8 if mock_success else 0.4
            mock_response_time = 2.0 + i * 0.1

            feedback_loop.record_feedback(
                user_id=f"user_{i % 5}",
                tool_name=list(feedback_loop.tool_metrics.keys())[
                    i % len(feedback_loop.tool_metrics)
                ],
                intent="technical",
                context={},
                feedback_type=FeedbackType.AUTOMATIC_DETECTION,
                feedback_channel=FeedbackChannel.IMPLICIT_MONITORING,
                execution_success=mock_success,
                response_time=mock_response_time,
                satisfaction_score=mock_satisfaction,
            )

        logger.info(f"📊 总反馈记录数: {len(feedback_loop.feedback_records)}")

        # 训练模型
        feedback_loop.train_feedback_predictor()

        # 分析反馈模式
        analysis = feedback_loop.analyze_feedback_patterns(days=30)
        logger.info("\n📈 反馈模式分析:")
        for key, value in analysis.items():
            if key not in ["error", "tool_performance", "user_patterns"]:
                logger.info(f"  {key}: {value}")

        # 预测优化需求
        tool_to_check = "code_analyzer"
        optimization_prob, explanation = feedback_loop.predict_optimization_need(
            tool_name=tool_to_check, user_id=user_id, intent="technical"
        )
        logger.info("\n🔮 优化需求预测:")
        logger.info(f"工具: {tool_to_check}")
        logger.info(f"优化概率: {optimization_prob:.3f}")
        logger.info(f"解释: {explanation}")

        # 保存模型
        feedback_loop.save_models()

        logger.info("🎉 工具效果反馈循环系统测试完成!")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
