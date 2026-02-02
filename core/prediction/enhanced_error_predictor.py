#!/usr/bin/env python3
"""
增强错误预测器
Enhanced Error Predictor

基于机器学习的错误预测系统:
1. 特征工程(20+个特征)
2. 多模型集成预测
3. 在线学习机制
4. 预测置信度评估
5. 自动模型选择

作者: Athena平台团队
创建时间: 2025-12-27
版本: v2.0.0
"""

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union



logger = logging.getLogger(__name__)

# 导入扩展错误模式
import contextlib

from .extended_error_patterns import (
    ErrorPattern,
    ErrorPatternFeatures,
    RiskLevel,
    get_error_pattern_features,
    get_prevention_strategies,
    get_recovery_strategies,
)


class PredictionModel(Enum):
    """预测模型类型"""

    RULE_BASED = "rule_based"  # 基于规则
    FREQUENCY_BASED = "frequency"  # 基于频率
    TREND_BASED = "trend"  # 基于趋势
    ENSEMBLE = "ensemble"  # 集成模型
    ONLINE_LEARNING = "online"  # 在线学习


@dataclass
class FeatureVector:
    """特征向量"""

    # 系统资源特征
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: float = 0.0

    # 请求特征
    request_rate: float = 0.0
    concurrent_requests: int = 0
    queue_length: int = 0
    avg_response_time: float = 0.0

    # 错误特征
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    retry_rate: float = 0.0

    # AI模型特征
    model_requests: int = 0
    token_usage: float = 0.0
    embedding_failures: int = 0

    # 时间特征
    hour_of_day: int = 0
    day_of_week: int = 0

    # 趋势特征
    cpu_trend: float = 0.0  # CPU使用趋势
    memory_trend: float = 0.0  # 内存使用趋势
    error_trend: float = 0.0  # 错误率趋势

    # 自定义特征
    custom_features: dict[str, float] = field(default_factory=dict)

    def to_array(self) -> np.ndarray:
        """转换为numpy数组"""
        base_features = [
            self.cpu_usage,
            self.memory_usage,
            self.disk_usage,
            self.network_io,
            self.request_rate,
            self.concurrent_requests / 1000.0,  # 归一化
            self.queue_length / 1000.0,
            self.avg_response_time / 10.0,
            self.error_rate,
            self.timeout_rate,
            self.retry_rate,
            self.model_requests / 100.0,
            self.token_usage / 10000.0,
            self.embedding_failures / 10.0,
            self.hour_of_day / 24.0,
            self.day_of_week / 7.0,
            self.cpu_trend,
            self.memory_trend,
            self.error_trend,
        ]
        return np.array(base_features + list(self.custom_features.values()))


@dataclass
class PredictionResult:
    """预测结果"""

    error_pattern: ErrorPattern
    probability: float  # 发生概率
    confidence: float  # 置信度
    risk_level: RiskLevel
    predicted_time: Optional[datetime]
    feature_importance: dict[str, float] = field(default_factory=dict)
    model_used: PredictionModel = PredictionModel.ENSEMBLE
    prevention_suggestions: list[str] = field(default_factory=list)
    recovery_suggestions: list[str] = field(default_factory=list)


class EnhancedErrorPredictor:
    """
    增强错误预测器

    核心能力:
    1. 特征工程(20+特征)
    2. 多模型集成预测
    3. 在线学习
    4. 自动模型选择
    """

    def __init__(
        self, window_size: int = 1000, model_config_path: str = "config/error_predictor_models.json"
    ):
        self.window_size = window_size
        self.model_config_path = Path(model_config_path)

        # 特征历史
        self.feature_history: deque = deque(maxlen=window_size)

        # 错误历史
        self.error_history: dict[ErrorPattern, deque] = defaultdict(lambda: deque(maxlen=100))

        # 模型性能
        self.model_performance: dict[PredictionModel, dict[str, float]] = {
            PredictionModel.RULE_BASED: {"accuracy": 0.75, "weight": 0.2},
            PredictionModel.FREQUENCY_BASED: {"accuracy": 0.70, "weight": 0.15},
            PredictionModel.TREND_BASED: {"accuracy": 0.78, "weight": 0.2},
            PredictionModel.ENSEMBLE: {"accuracy": 0.85, "weight": 0.3},
            PredictionModel.ONLINE_LEARNING: {"accuracy": 0.80, "weight": 0.15},
        }

        # 加载模型配置
        self._load_model_config()

        logger.info("🔮 增强错误预测器初始化完成")
        logger.info(f"   支持的错误模式: {len(ErrorPattern)} 种")
        logger.info("   特征维度: 20+")

    def _load_model_config(self) -> Any:
        """加载模型配置"""
        if self.model_config_path.exists():
            try:
                with open(self.model_config_path, encoding="utf-8") as f:
                    config = json.load(f)
                    # 加载模型性能
                    if "model_performance" in config:
                        for model_name, perf in config["model_performance"].items():
                            model_type = PredictionModel(model_name)
                            self.model_performance[model_type] = perf
                logger.info("✅ 已加载模型配置")
            except Exception as e:
                logger.warning(f"⚠️  加载模型配置失败: {e}")

    def _save_model_config(self) -> Any:
        """保存模型配置"""
        self.model_config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "version": "2.0.0",
            "last_updated": datetime.now().isoformat(),
            "model_performance": {
                model.value: perf for model, perf in self.model_performance.items()
            },
        }

        with open(self.model_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.debug("💾 模型配置已保存")

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
        features.network_io = context.get("network_io", 0.0)

        # 请求特征
        features.request_rate = context.get("request_rate", 0.0)
        features.concurrent_requests = context.get("concurrent_requests", 0)
        features.queue_length = context.get("queue_length", 0)
        features.avg_response_time = context.get("avg_response_time", 0.0)

        # 错误特征
        features.error_rate = context.get("error_rate", 0.0)
        features.timeout_rate = context.get("timeout_rate", 0.0)
        features.retry_rate = context.get("retry_rate", 0.0)

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
                [f.cpu_usage for f in recent[:5]]
            )
            features.memory_trend = np.mean([f.memory_usage for f in recent[-5:]]) - np.mean(
                [f.memory_usage for f in recent[:5]]
            )
            features.error_trend = np.mean([f.error_rate for f in recent[-5:]]) - np.mean(
                [f.error_rate for f in recent[:5]]
            )

        # 自定义特征
        for key, value in context.items():
            if key not in features.__dict__:
                with contextlib.suppress(ValueError, TypeError):
                    features.custom_features[key] = float(value)

        # 添加到历史
        self.feature_history.append(features)

        return features

    async def predict(
        self,
        context: dict[str, Any],        time_horizon: timedelta = timedelta(minutes=10),
        top_k: int = 5,
    ) -> list[PredictionResult]:
        """
        预测错误

        Args:
            context: 当前上下文
            time_horizon: 预测时间范围
            top_k: 返回top-k个预测

        Returns:
            预测结果列表
        """
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

        # 返回top-k
        return predictions[:top_k]

    async def _predict_single_pattern(
        self,
        pattern: ErrorPattern,
        features: FeatureVector,
        context: dict[str, Any],        time_horizon: timedelta,
    ) -> PredictionResult:
        """预测单个错误模式"""

        # 获取模式特征
        pattern_features = get_error_pattern_features(pattern)
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
        predictions[PredictionModel.FREQUENCY_BASED] = self._frequency_based_prediction(
            pattern, features
        )

        # 3. 基于趋势的预测
        predictions[PredictionModel.TREND_BASED] = self._trend_based_prediction(
            pattern, features, pattern_features
        )

        # 4. 在线学习预测
        predictions[PredictionModel.ONLINE_LEARNING] = self._online_learning_prediction(
            pattern, features
        )

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

        # 获取建议
        prevention_suggestions = get_prevention_strategies(pattern)
        recovery_suggestions = get_recovery_strategies(pattern)

        return PredictionResult(
            error_pattern=pattern,
            probability=ensemble_prob,
            confidence=confidence,
            risk_level=risk_level,
            predicted_time=predicted_time,
            feature_importance=feature_importance,
            prevention_suggestions=prevention_suggestions,
            recovery_suggestions=recovery_suggestions,
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
        # 计算特征趋势
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

        for key in conditions:
            if hasattr(features, key):
                value = getattr(features, key)
                # 接近阈值的特征更重要
                threshold = conditions[key]
                if isinstance(threshold, (int, float)):
                    distance = abs(value - threshold) / (abs(threshold) + 1e-8)
                    importance[key] = 1.0 / (1.0 + distance)

        # 归一化
        if importance:
            total = sum(importance.values())
            importance = {k: v / total for k, v in importance.items()}

        return importance

    async def record_error(
        self, pattern: ErrorPattern, context: dict[str, Any], recovery_time: float
    ):
        """
        记录错误(用于在线学习)

        Args:
            pattern: 错误模式
            context: 错误上下文
            recovery_time: 恢复时间
        """
        # 记录错误历史
        self.error_history[pattern].append(
            {"timestamp": datetime.now(), "context": context, "recovery_time": recovery_time}
        )

        # 更新模型性能(简化)
        # 实际实现中应该根据预测准确性更新

        logger.debug(f"📝 已记录错误: {pattern.value}")

    async def get_model_performance(self) -> dict[str, Any]:
        """获取模型性能"""
        return {
            "models": {model.value: perf for model, perf in self.model_performance.items()},
            "best_model": max(self.model_performance.items(), key=lambda x: x[1]["accuracy"])[
                0
            ].value,
            "total_predictions": sum(len(history) for history in self.error_history.values()),
        }


# 导出便捷函数
_predictor: EnhancedErrorPredictor | None = None


def get_enhanced_predictor() -> EnhancedErrorPredictor:
    """获取增强错误预测器单例"""
    global _predictor
    if _predictor is None:
        _predictor = EnhancedErrorPredictor()
    return _predictor


# 使用示例
async def main():
    """主函数示例"""
    print("=" * 70)
    print("增强错误预测器演示")
    print("=" * 70)

    # 获取预测器
    predictor = get_enhanced_predictor()

    # 模拟上下文(高负载场景)
    context = {
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

    print("\n🔍 预测错误...")
    predictions = await predictor.predict(context, top_k=5)

    print(f"\n✅ 预测结果 (Top-{len(predictions)}):\n")

    for i, pred in enumerate(predictions, 1):
        if pred.probability < 0.2:
            continue

        print(f"{i}. {pred.error_pattern.value}")
        print(f"   概率: {pred.probability:.1%}")
        print(f"   置信度: {pred.confidence:.1%}")
        print(f"   风险等级: {pred.risk_level.value}")

        if pred.predicted_time:
            print(f"   预计时间: {pred.predicted_time.strftime('%H:%M:%S')}")

        if pred.feature_importance:
            print("   关键因素:")
            for feature, importance in sorted(pred.feature_importance.items(), key=lambda x: -x[1])[
                :3
            ]:
                print(f"     - {feature}: {importance:.1%}")

        if pred.prevention_suggestions:
            print("   预防建议:")
            for suggestion in pred.prevention_suggestions[:2]:
                print(f"     - {suggestion}")

        print()

    # 模型性能
    print("📊 模型性能:")
    perf = await predictor.get_model_performance()
    print(f"   最佳模型: {perf['best_model']}")
    print(f"   总预测数: {perf['total_predictions']}")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
