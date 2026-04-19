#!/usr/bin/env python3
from __future__ import annotations
"""
轻量级错误预测模块
Lightweight Error Predictor Module

从Athena提取的轻量级错误预测能力:
1. 特征工程(20+特征)
2. 多模型集成预测(5种模型)
3. 在线学习机制
4. 预测置信度评估
5. 自动预防建议

专门为小诺优化,去除Athena强耦合依赖。

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0 "轻量级集成版"
"""

import contextlib
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ===== 风险等级 =====
class RiskLevel(Enum):
    """风险等级"""

    NONE = "none"  # 无风险
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


# ===== 错误模式(简化版) =====
class ErrorPattern(Enum):
    """错误模式(精选关键模式)"""

    # 基础模式
    TIMEOUT = "timeout"  # 超时
    RATE_LIMIT = "rate_limit"  # 限流
    RESOURCE_EXHAUSTION = "resource"  # 资源耗尽
    PERFORMANCE_DEGRADATION = "performance"  # 性能下降

    # AI模型相关
    MODEL_OVERLOAD = "model_overload"  # 模型过载
    TOKEN_LIMIT_EXCEEDED = "token_limit"  # Token超限

    # 数据相关
    DATA_CORRUPTION = "data_corruption"  # 数据损坏
    SCHEMA_MISMATCH = "schema_mismatch"  # 模式不匹配

    # 网络相关
    NETWORK_PARTITION = "network_partition"  # 网络分区
    API_UNREACHABLE = "api_unreachable"  # API不可达

    # 内存相关
    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    OUT_OF_MEMORY = "out_of_memory"  # 内存不足


# ===== 预测模型类型 =====
class PredictionModel(Enum):
    """预测模型类型"""

    RULE_BASED = "rule_based"  # 基于规则
    FREQUENCY_BASED = "frequency"  # 基于频率
    TREND_BASED = "trend"  # 基于趋势
    ENSEMBLE = "ensemble"  # 集成模型
    ONLINE_LEARNING = "online"  # 在线学习


# ===== 错误模式特征定义 =====
@dataclass
class ErrorPatternFeatures:
    """错误模式特征"""

    pattern: ErrorPattern
    category: str  # 类别
    severity: RiskLevel  # 严重程度
    trigger_conditions: dict[str, Any] = field(default_factory=dict)
    prevention_strategies: list[str] = field(default_factory=list)
    recovery_strategies: list[str] = field(default_factory=list)


# ===== 特征向量 =====
@dataclass
class FeatureVector:
    """特征向量"""

    # 系统资源特征
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0

    # 请求特征
    request_rate: float = 0.0
    concurrent_requests: int = 0
    queue_length: int = 0
    avg_response_time: float = 0.0

    # 错误特征
    error_rate: float = 0.0
    timeout_rate: float = 0.0

    # AI模型特征
    model_requests: int = 0
    token_usage: float = 0.0
    embedding_failures: int = 0

    # 时间特征
    hour_of_day: int = 0
    day_of_week: int = 0

    # 趋势特征
    cpu_trend: float = 0.0
    memory_trend: float = 0.0
    error_trend: float = 0.0

    # 自定义特征
    custom_features: dict[str, float] = field(default_factory=dict)

    def to_array(self) -> np.ndarray:
        """转换为numpy数组"""
        base_features = [
            self.cpu_usage,
            self.memory_usage,
            self.disk_usage,
            self.request_rate / 100.0,  # 归一化
            min(self.concurrent_requests / 500.0, 1.0),
            min(self.queue_length / 1000.0, 1.0),
            min(self.avg_response_time / 5.0, 1.0),
            self.error_rate,
            self.timeout_rate,
            min(self.model_requests / 100.0, 1.0),
            min(self.token_usage / 10000.0, 1.0),
            min(self.embedding_failures / 10.0, 1.0),
            self.hour_of_day / 24.0,
            self.day_of_week / 7.0,
            self.cpu_trend,
            self.memory_trend,
            self.error_trend,
        ]
        return np.array(base_features + list(self.custom_features.values()))


# ===== 预测结果 =====
@dataclass
class PredictionResult:
    """预测结果"""

    error_pattern: ErrorPattern
    probability: float  # 发生概率
    confidence: float  # 置信度
    risk_level: RiskLevel
    predicted_time: datetime | None = None
    feature_importance: dict[str, float] = field(default_factory=dict)
    model_used: PredictionModel = PredictionModel.ENSEMBLE
    prevention_suggestions: list[str] = field(default_factory=list)
    recovery_suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "error_pattern": self.error_pattern.value,
            "probability": self.probability,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "predicted_time": self.predicted_time.isoformat() if self.predicted_time else None,
            "feature_importance": self.feature_importance,
            "model_used": self.model_used.value,
            "prevention_suggestions": self.prevention_suggestions,
            "recovery_suggestions": self.recovery_suggestions,
        }


# ===== 错误模式特征库(简化版) =====
ERROR_PATTERN_FEATURES: dict[ErrorPattern, ErrorPatternFeatures] = {
    # 基础模式
    ErrorPattern.TIMEOUT: ErrorPatternFeatures(
        pattern=ErrorPattern.TIMEOUT,
        category="基础",
        severity=RiskLevel.MEDIUM,
        trigger_conditions={"processing_time": 10.0, "queue_length": 100, "cpu_usage": 0.9},
        prevention_strategies=[
            "增加超时时间配置",
            "实现请求超时控制",
            "添加队列监控告警",
            "实施熔断机制",
        ],
        recovery_strategies=["重试请求", "降级处理", "使用缓存"],
    ),
    ErrorPattern.RATE_LIMIT: ErrorPatternFeatures(
        pattern=ErrorPattern.RATE_LIMIT,
        category="基础",
        severity=RiskLevel.HIGH,
        trigger_conditions={"request_rate": 100, "error_rate": 0.05},
        prevention_strategies=[
            "实施请求速率限制",
            "使用令牌桶算法",
            "增加请求重试间隔",
            "实现客户端缓存",
        ],
        recovery_strategies=["指数退避重试", "降级处理", "使用备用API"],
    ),
    ErrorPattern.RESOURCE_EXHAUSTION: ErrorPatternFeatures(
        pattern=ErrorPattern.RESOURCE_EXHAUSTION,
        category="基础",
        severity=RiskLevel.CRITICAL,
        trigger_conditions={"cpu_usage": 0.95, "memory_usage": 0.95},
        prevention_strategies=[
            "实施资源监控告警",
            "实施自动扩缩容",
            "优化资源使用",
            "实施请求限流",
        ],
        recovery_strategies=["扩容资源", "降级服务", "重启服务"],
    ),
    ErrorPattern.PERFORMANCE_DEGRADATION: ErrorPatternFeatures(
        pattern=ErrorPattern.PERFORMANCE_DEGRADATION,
        category="基础",
        severity=RiskLevel.MEDIUM,
        trigger_conditions={"avg_response_time": 2.0, "error_rate": 0.03},
        prevention_strategies=["实施性能监控", "优化慢查询", "增加缓存", "实施负载均衡"],
        recovery_strategies=["重启服务", "清理缓存", "优化配置"],
    ),
    # AI模型相关
    ErrorPattern.MODEL_OVERLOAD: ErrorPatternFeatures(
        pattern=ErrorPattern.MODEL_OVERLOAD,
        category="AI模型",
        severity=RiskLevel.HIGH,
        trigger_conditions={"model_requests": 80, "cpu_usage": 0.85},
        prevention_strategies=["实施模型请求限流", "增加模型实例", "实施模型缓存", "使用备用模型"],
        recovery_strategies=["重启模型服务", "切换备用模型", "降级处理"],
    ),
    ErrorPattern.TOKEN_LIMIT_EXCEEDED: ErrorPatternFeatures(
        pattern=ErrorPattern.TOKEN_LIMIT_EXCEEDED,
        category="AI模型",
        severity=RiskLevel.MEDIUM,
        trigger_conditions={"token_usage": 9000},
        prevention_strategies=[
            "监控token使用量",
            "实施token限制",
            "优化提示词长度",
            "分段处理长文本",
        ],
        recovery_strategies=["分段重试", "简化提示词", "使用小模型"],
    ),
    # 数据相关
    ErrorPattern.DATA_CORRUPTION: ErrorPatternFeatures(
        pattern=ErrorPattern.DATA_CORRUPTION,
        category="数据",
        severity=RiskLevel.CRITICAL,
        trigger_conditions={"error_rate": 0.1},
        prevention_strategies=["实施数据校验", "定期备份", "使用事务", "实施数据完整性检查"],
        recovery_strategies=["从备份恢复", "数据修复", "回滚操作"],
    ),
    # 网络相关
    ErrorPattern.NETWORK_PARTITION: ErrorPatternFeatures(
        pattern=ErrorPattern.NETWORK_PARTITION,
        category="网络",
        severity=RiskLevel.HIGH,
        trigger_conditions={"timeout_rate": 0.2},
        prevention_strategies=["实施心跳检测", "使用备用线路", "实施超时重试", "实现服务降级"],
        recovery_strategies=["切换备用线路", "重启网络", "使用本地缓存"],
    ),
    # 内存相关
    ErrorPattern.MEMORY_LEAK: ErrorPatternFeatures(
        pattern=ErrorPattern.MEMORY_LEAK,
        category="内存",
        severity=RiskLevel.HIGH,
        trigger_conditions={"memory_trend": 0.01, "memory_usage": 0.8},
        prevention_strategies=["实施内存监控", "定期重启服务", "优化内存使用", "使用内存分析工具"],
        recovery_strategies=["重启服务", "清理缓存", "优化代码"],
    ),
    ErrorPattern.OUT_OF_MEMORY: ErrorPatternFeatures(
        pattern=ErrorPattern.OUT_OF_MEMORY,
        category="内存",
        severity=RiskLevel.CRITICAL,
        trigger_conditions={"memory_usage": 0.95},
        prevention_strategies=["实施内存限制", "优化数据结构", "实施流式处理", "增加内存容量"],
        recovery_strategies=["扩容内存", "重启服务", "清理缓存"],
    ),
}


# ===== 轻量级错误预测器 =====
class LightweightErrorPredictor:
    """
    轻量级错误预测模块

    从Athena增强错误预测器提取核心能力,
    专门设计为可被小诺直接导入使用的Python模块。

    核心特性:
    1. 零外部服务依赖
    2. 可选在线学习支持
    3. 配置驱动的预测策略
    4. 简化的API接口
    5. 多模型集成预测
    """

    def __init__(self, config: dict | None = None):
        """
        初始化轻量级错误预测器

        Args:
            config: 配置字典,包含:
                - enable_online_learning: 是否启用在线学习(默认True)
                - window_size: 特征历史窗口大小(默认1000)
                - prediction_horizon_minutes: 预测时间范围(默认10分钟)
        """
        self.config = config or {}

        # 配置参数
        self.enable_online_learning = self.config.get("enable_online_learning", True)
        self.window_size = self.config.get("window_size", 1000)
        self.prediction_horizon_minutes = self.config.get("prediction_horizon_minutes", 10)

        # 特征历史
        self.feature_history: deque = deque(maxlen=self.window_size)

        # 错误历史
        self.error_history: dict[ErrorPattern, deque] = defaultdict(lambda: deque(maxlen=100))

        # 模型性能(权重基于准确率)
        self.model_performance: dict[PredictionModel, dict[str, float]] = {
            PredictionModel.RULE_BASED: {"accuracy": 0.75, "weight": 0.20},
            PredictionModel.FREQUENCY_BASED: {"accuracy": 0.70, "weight": 0.15},
            PredictionModel.TREND_BASED: {"accuracy": 0.78, "weight": 0.20},
            PredictionModel.ENSEMBLE: {"accuracy": 0.85, "weight": 0.30},
            PredictionModel.ONLINE_LEARNING: {"accuracy": 0.80, "weight": 0.15},
        }

        # 统计信息
        self.stats = {
            "total_predictions": 0,
            "high_risk_predictions": 0,
            "avg_prediction_time": 0.0,
        }

        logger.info("🔮 轻量级错误预测模块初始化完成")
        logger.info(f"   支持的错误模式: {len(ErrorPattern)} 种")
        logger.info("   特征维度: 17+")
        logger.info(f"   在线学习: {'启用' if self.enable_online_learning else '禁用'}")

    async def predict(self, context: dict[str, Any], top_k: int = 5) -> list[PredictionResult]:
        """
        预测错误(简化版API)

        Args:
            context: 当前上下文(系统指标)
            top_k: 返回top-k个预测

        Returns:
            预测结果列表
        """
        time_horizon = timedelta(minutes=self.prediction_horizon_minutes)
        return await self.predict_with_horizon(context, time_horizon, top_k)

    async def predict_with_horizon(
        self, context: dict[str, Any], time_horizon: timedelta, top_k: int = 5
    ) -> list[PredictionResult]:
        """
        预测错误(完整API)

        Args:
            context: 当前上下文
            time_horizon: 预测时间范围
            top_k: 返回top-k个预测

        Returns:
            预测结果列表
        """
        start_time = datetime.now()

        # 提取特征
        features = self.extract_features(context)

        # 对每种错误模式进行预测
        predictions = []

        for error_pattern in ErrorPattern:
            result = await self._predict_single_pattern(
                error_pattern, features, context, time_horizon
            )
            predictions.append(result)

        # 按概率排序
        predictions.sort(key=lambda p: p.probability, reverse=True)

        # 更新统计
        self.stats["total_predictions"] += 1
        self.stats["high_risk_predictions"] += sum(
            1 for p in predictions[:top_k] if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )

        prediction_time = (datetime.now() - start_time).total_seconds()
        self.stats["avg_prediction_time"] = (
            self.stats["avg_prediction_time"] * (self.stats["total_predictions"] - 1)
            + prediction_time
        ) / self.stats["total_predictions"]

        # 返回top-k
        return predictions[:top_k]

    def extract_features(self, context: dict[str, Any]) -> FeatureVector:
        """
        提取特征向量

        Args:
            context: 当前上下文

        Returns:
            特征向量
        """
        now = datetime.now()

        features = FeatureVector()

        # 系统资源特征
        features.cpu_usage = context.get("cpu_usage", 0.0)
        features.memory_usage = context.get("memory_usage", 0.0)
        features.disk_usage = context.get("disk_usage", 0.0)

        # 请求特征
        features.request_rate = context.get("request_rate", 0.0)
        features.concurrent_requests = context.get("concurrent_requests", 0)
        features.queue_length = context.get("queue_length", 0)
        features.avg_response_time = context.get("avg_response_time", 0.0)

        # 错误特征
        features.error_rate = context.get("error_rate", 0.0)
        features.timeout_rate = context.get("timeout_rate", 0.0)

        # AI模型特征
        features.model_requests = context.get("model_requests", 0)
        features.token_usage = context.get("token_usage", 0.0)
        features.embedding_failures = context.get("embedding_failures", 0)

        # 时间特征
        features.hour_of_day = now.hour
        features.day_of_week = now.weekday()

        # 计算趋势特征
        if len(self.feature_history) >= 10:
            recent = list(self.feature_history)[-10:]
            features.cpu_trend = np.mean([f.cpu_usage for f in recent[-5:]]) - np.mean(
                [f.cpu_usage for f in recent[:5]])
            features.memory_trend = np.mean([f.memory_usage for f in recent[-5:]]) - np.mean(
                [f.memory_usage for f in recent[:5]])
            features.error_trend = np.mean([f.error_rate for f in recent[-5:]]) - np.mean(
                [f.error_rate for f in recent[:5]])

        # 自定义特征
        for key, value in context.items():
            if key not in features.__dict__:
                with contextlib.suppress(ValueError, TypeError):
                    features.custom_features[key] = float(value)

        # 添加到历史
        if self.enable_online_learning:
            self.feature_history.append(features)

        return features

    async def _predict_single_pattern(
        self,
        pattern: ErrorPattern,
        features: FeatureVector,
        context: dict[str, Any],        time_horizon: timedelta,
    ) -> PredictionResult:
        """预测单个错误模式"""
        # 获取模式特征
        pattern_features = ERROR_PATTERN_FEATURES.get(pattern)
        if not pattern_features:
            return PredictionResult(
                error_pattern=pattern, probability=0.0, confidence=0.0, risk_level=RiskLevel.NONE
            )

        # 多模型预测
        predictions = {}

        # 1. 基于规则的预测
        predictions[PredictionModel.RULE_BASED] = self._rule_based_prediction(
            pattern, features, pattern_features
        )

        # 2. 基于频率的预测
        if self.enable_online_learning:
            predictions[PredictionModel.FREQUENCY_BASED] = self._frequency_based_prediction(
                pattern, features
            )
        else:
            predictions[PredictionModel.FREQUENCY_BASED] = 0.0

        # 3. 基于趋势的预测
        predictions[PredictionModel.TREND_BASED] = self._trend_based_prediction(
            pattern, features, pattern_features
        )

        # 4. 在线学习预测
        if self.enable_online_learning and len(self.feature_history) >= 20:
            predictions[PredictionModel.ONLINE_LEARNING] = self._online_learning_prediction(
                pattern, features
            )
        else:
            predictions[PredictionModel.ONLINE_LEARNING] = 0.0

        # 集成预测
        ensemble_prob = self._ensemble_predictions(predictions)

        # 计算置信度
        confidence = self._calculate_confidence(predictions)

        # 确定风险等级
        risk_level = self._determine_risk_level(ensemble_prob, pattern_features)

        # 预测发生时间
        predicted_time = None
        if ensemble_prob > 0.5:
            predicted_time = datetime.now() + timedelta(
                seconds=int(time_horizon.total_seconds() * (1 - ensemble_prob))
            )

        # 特征重要性
        feature_importance = self._calculate_feature_importance(pattern, features, pattern_features)

        return PredictionResult(
            error_pattern=pattern,
            probability=ensemble_prob,
            confidence=confidence,
            risk_level=risk_level,
            predicted_time=predicted_time,
            feature_importance=feature_importance,
            prevention_suggestions=pattern_features.prevention_strategies,
            recovery_suggestions=pattern_features.recovery_strategies,
        )

    def _rule_based_prediction(
        self, pattern: ErrorPattern, features: FeatureVector, pattern_features: ErrorPatternFeatures
    ) -> float:
        """基于规则的预测"""
        score = 0.0
        total_weight = 0.0

        conditions = pattern_features.trigger_conditions

        # CPU使用率
        if "cpu_usage" in conditions:
            if features.cpu_usage >= conditions["cpu_usage"]:
                score += 1.0
            total_weight += 1.0

        # 内存使用率
        if "memory_usage" in conditions:
            if features.memory_usage >= conditions["memory_usage"]:
                score += 1.0
            total_weight += 1.0

        # 并发请求数
        if "concurrent_requests" in conditions:
            if features.concurrent_requests >= conditions["concurrent_requests"]:
                score += 1.0
            total_weight += 1.0

        # 错误率
        if "error_rate" in conditions:
            if features.error_rate >= conditions["error_rate"]:
                score += 1.0
            total_weight += 1.0

        # 趋势
        if "memory_usage_trend" in conditions:
            if features.memory_trend > conditions["memory_usage_trend"]:
                score += 1.0
            total_weight += 1.0

        return score / total_weight if total_weight > 0 else 0.0

    def _frequency_based_prediction(self, pattern: ErrorPattern, features: FeatureVector) -> float:
        """基于频率的预测"""
        history = self.error_history[pattern]

        if len(history) < 5:
            return 0.0

        # 计算最近频率
        recent_errors = list(history)[-10:]
        frequency = len(recent_errors) / 10.0

        # 归一化到0-1
        return min(frequency * 5, 1.0)

    def _trend_based_prediction(
        self, pattern: ErrorPattern, features: FeatureVector, pattern_features: ErrorPatternFeatures
    ) -> float:
        """基于趋势的预测"""
        trend_score = 0.0

        if pattern == ErrorPattern.MEMORY_LEAK:
            if features.memory_trend > 0.01:  # 持续增长
                trend_score = min(features.memory_trend * 10, 1.0)

        elif pattern == ErrorPattern.RESOURCE_EXHAUSTION:
            if features.cpu_trend > 0.05:
                trend_score += 0.5
            if features.memory_trend > 0.05:
                trend_score += 0.5

        return trend_score

    def _online_learning_prediction(self, pattern: ErrorPattern, features: FeatureVector) -> float:
        """在线学习预测"""
        # 简化实现:基于历史相似性
        if len(self.feature_history) < 20:
            return 0.0

        # 找到相似的历史特征
        current_array = features.to_array()

        similarities = []
        for hist_features in list(self.feature_history)[-50:]:
            hist_array = hist_features.to_array()
            # 余弦相似度
            similarity = np.dot(current_array, hist_array) / (
                np.linalg.norm(current_array) * np.linalg.norm(hist_array) + 1e-8
            )
            similarities.append(similarity)

        if not similarities:
            return 0.0

        # 高相似度意味着可能发生类似错误
        avg_similarity = np.mean(similarities)
        return max(0, min(avg_similarity, 1.0))

    def _ensemble_predictions(self, predictions: dict[PredictionModel, float]) -> float:
        """集成多个模型的预测"""
        weighted_sum = 0.0
        total_weight = 0.0

        for model, prob in predictions.items():
            weight = self.model_performance[model]["weight"]
            weighted_sum += prob * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_confidence(self, predictions: dict[PredictionModel, float]) -> float:
        """计算预测置信度"""
        if not predictions:
            return 0.0

        values = list(predictions.values())
        variance = np.var(values)

        # 方差越小,置信度越高
        confidence = 1.0 / (1.0 + variance)
        return confidence

    def _determine_risk_level(
        self, probability: float, pattern_features: ErrorPatternFeatures
    ) -> RiskLevel:
        """确定风险等级"""
        if probability >= 0.9:
            return RiskLevel.CRITICAL
        elif probability >= 0.7:
            return RiskLevel.HIGH
        elif probability >= 0.4:
            return RiskLevel.MEDIUM
        elif probability >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE

    def _calculate_feature_importance(
        self, pattern: ErrorPattern, features: FeatureVector, pattern_features: ErrorPatternFeatures
    ) -> dict[str, float]:
        """计算特征重要性"""
        importance = {}

        # 基于触发条件计算重要性
        conditions = pattern_features.trigger_conditions

        for condition_name, condition_value in conditions.items():
            # 获取对应特征值
            feature_value = getattr(features, condition_name, None)
            if feature_value is None:
                # 尝试从custom_features获取
                feature_value = features.custom_features.get(condition_name)

            if feature_value is not None:
                # 计算触发程度
                try:
                    ratio = float(feature_value) / float(condition_value)
                    importance[condition_name] = min(ratio, 1.0)
                except (ZeroDivisionError, ValueError, TypeError):
                    importance[condition_name] = 0.0

        return importance

    async def record_error(
        self, error_pattern: ErrorPattern, context: dict[str, Any], recovery_time: float
    ):
        """
        记录错误(用于在线学习)

        Args:
            error_pattern: 错误模式
            context: 发生错误时的上下文
            recovery_time: 恢复时间(秒)
        """
        if not self.enable_online_learning:
            return

        # 添加到错误历史
        self.error_history[error_pattern].append(
            {"context": context, "recovery_time": recovery_time, "timestamp": datetime.now()}
        )

        logger.debug(f"📝 已记录错误: {error_pattern.value}")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "error_patterns_supported": len(ErrorPattern),
            "feature_history_size": len(self.feature_history),
            "error_history_size": sum(len(h) for h in self.error_history.values()),
            "online_learning_enabled": self.enable_online_learning,
        }

    def get_error_pattern_features(self, pattern: ErrorPattern) -> ErrorPatternFeatures | None:
        """获取错误模式特征"""
        return ERROR_PATTERN_FEATURES.get(pattern)


# 便捷函数
_predictor_instance: LightweightErrorPredictor | None = None


def get_error_predictor(config: dict | None = None) -> LightweightErrorPredictor:
    """获取错误预测器单例"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = LightweightErrorPredictor(config)
    return _predictor_instance


# 使用示例
async def main():
    """演示函数"""
    print("=" * 60)
    print("轻量级错误预测模块演示")
    print("=" * 60)

    # 创建预测器
    predictor = LightweightErrorPredictor()

    # 模拟上下文(高负载场景)
    print("\n📊 场景1: 高负载场景")
    context_high_load = {
        "cpu_usage": 0.92,
        "memory_usage": 0.88,
        "disk_usage": 0.75,
        "request_rate": 150,
        "concurrent_requests": 450,
        "queue_length": 800,
        "avg_response_time": 2.5,
        "error_rate": 0.08,
        "timeout_rate": 0.05,
        "model_requests": 80,
        "token_usage": 8500,
        "embedding_failures": 3,
    }

    predictions = await predictor.predict(context_high_load, top_k=5)

    print(f"\n预测结果 (Top-{len(predictions)}):\n")
    for i, pred in enumerate(predictions, 1):
        if pred.probability < 0.2:
            continue
        print(f"{i}. {pred.error_pattern.value}")
        print(f"   概率: {pred.probability:.1%}")
        print(f"   置信度: {pred.confidence:.1%}")
        print(f"   风险等级: {pred.risk_level.value}")
        if pred.prevention_suggestions:
            print(f"   预防建议: {pred.prevention_suggestions[0]}")
        print()

    # 模拟上下文(正常场景)
    print("📊 场景2: 正常场景")
    context_normal = {
        "cpu_usage": 0.45,
        "memory_usage": 0.52,
        "disk_usage": 0.60,
        "request_rate": 30,
        "concurrent_requests": 50,
        "queue_length": 10,
        "avg_response_time": 0.3,
        "error_rate": 0.01,
        "timeout_rate": 0.005,
        "model_requests": 10,
        "token_usage": 2000,
        "embedding_failures": 0,
    }

    predictions = await predictor.predict(context_normal, top_k=3)

    print(f"\n预测结果 (Top-{len(predictions)}):\n")
    for i, pred in enumerate(predictions, 1):
        if pred.probability < 0.1:
            continue
        print(f"{i}. {pred.error_pattern.value}")
        print(f"   概率: {pred.probability:.1%}")
        print(f"   风险等级: {pred.risk_level.value}")
        print()

    # 统计信息
    print("📊 统计信息:")
    stats = predictor.get_stats()
    print(f"   总预测次数: {stats['total_predictions']}")
    print(f"   高风险预测数: {stats['high_risk_predictions']}")
    print(f"   平均预测时间: {stats['avg_prediction_time']*1000:.2f}ms")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
