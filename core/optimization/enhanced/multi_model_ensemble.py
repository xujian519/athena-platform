#!/usr/bin/env python3
from __future__ import annotations
"""
多模型集成系统 (Multi-Model Ensemble System)
智能集成多个模型,提升整体预测准确性和鲁棒性

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 集成准确率 92% → 96%
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..utils import normalize_dict_values

logger = logging.getLogger(__name__)


class EnsembleMethod(str, Enum):
    """集成方法"""

    VOTING = "voting"  # 投票法
    WEIGHTED_VOTING = "weighted_voting"  # 加权投票
    BAGGING = "bagging"  # Bagging
    BOOSTING = "boosting"  # Boosting
    STACKING = "stacking"  # Stacking
    BLENDING = "blending"  # Blending


class ModelType(str, Enum):
    """模型类型"""

    CLASSIFICATION = "classification"  # 分类模型
    REGRESSION = "regression"  # 回归模型
    SEQUENTIAL = "sequential"  # 序列模型
    GENERATIVE = "generative"  # 生成模型


@dataclass
class ModelPrediction:
    """模型预测结果"""

    model_id: str
    prediction: Any
    confidence: float
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """集成结果"""

    final_prediction: Any
    confidence: float
    method: EnsembleMethod
    individual_predictions: list[ModelPrediction]
    weight_distribution: dict[str, float]
    improvement: float  # 相比最佳单个模型的提升
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ModelPerformance:
    """模型性能"""

    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    avg_latency_ms: float
    success_rate: float
    total_predictions: int
    last_updated: datetime = field(default_factory=datetime.now)


class BaseEnsembleModel:
    """集成模型基类"""

    def __init__(self, model_id: str, model_type: ModelType):
        self.model_id = model_id
        self.model_type = model_type
        self.performance = ModelPerformance(
            model_id=model_id,
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            avg_latency_ms=0.0,
            success_rate=0.0,
            total_predictions=0,
        )

    async def predict(
        self, input_data: dict[str, Any], context: Optional[dict[str, Any]] = None
    ) -> ModelPrediction:
        """
        模型预测(子类实现)

        Args:
            input_data: 输入数据
            context: 上下文

        Returns:
            预测结果
        """
        raise NotImplementedError


class MultiModelEnsemble:
    """
    多模型集成系统

    功能:
    1. 多模型管理
    2. 智能权重分配
    3. 多种集成方法
    4. 性能监控
    5. 动态模型选择
    """

    def __init__(self, default_method: EnsembleMethod = EnsembleMethod.WEIGHTED_VOTING):
        self.name = "多模型集成系统"
        self.version = "2.0.0"
        self.default_method = default_method

        # 模型注册表
        self.models: dict[str, BaseEnsembleModel] = {}

        # 模型权重
        self.model_weights: dict[str, float] = {}

        # 性能历史
        self.performance_history: list[ModelPerformance] = []

        # 集成历史
        self.ensemble_history: list[EnsembleResult] = []

        # 统计信息
        self.stats = {
            "total_ensembles": 0,
            "accuracy_improvement": 0.0,
            "avg_latency_ms": 0.0,
            "best_model": None,
            "ensemble_accuracy": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (方法: {default_method.value})")

    def register_model(self, model: BaseEnsembleModel, initial_weight: float = 1.0) -> None:
        """
        注册模型

        Args:
            model: 模型实例
            initial_weight: 初始权重
        """
        self.models[model.model_id] = model
        self.model_weights[model.model_id] = initial_weight

        logger.info(f"📝 注册模型: {model.model_id} (权重: {initial_weight:.2f})")

    async def predict(
        self,
        input_data: dict[str, Any],        method: EnsembleMethod | None = None,
        context: Optional[dict[str, Any]] = None,
    ) -> EnsembleResult:
        """
        集成预测

        Args:
            input_data: 输入数据
            method: 集成方法
            context: 上下文

        Returns:
            集成结果
        """
        self.stats["total_ensembles"] += 1

        method = method or self.default_method

        # 1. 获取所有模型的预测
        individual_predictions = await self._get_individual_predictions(input_data, context)

        # 2. 根据方法集成
        if method == EnsembleMethod.VOTING:
            result = await self._voting_ensemble(individual_predictions)
        elif method == EnsembleMethod.WEIGHTED_VOTING:
            result = await self._weighted_voting_ensemble(individual_predictions)
        elif method == EnsembleMethod.BAGGING:
            result = await self._bagging_ensemble(individual_predictions, input_data)
        elif method == EnsembleMethod.STACKING:
            result = await self._stacking_ensemble(individual_predictions, input_data)
        elif method == EnsembleMethod.BLENDING:
            result = await self._blending_ensemble(individual_predictions, input_data)
        else:
            result = await self._weighted_voting_ensemble(individual_predictions)

        # 3. 记录历史
        self.ensemble_history.append(result)

        # 4. 更新统计
        await self._update_statistics(result)

        return result

    async def _get_individual_predictions(
        self, input_data: dict[str, Any], context: dict[str, Any]
    ) -> list[ModelPrediction]:
        """获取所有模型的预测"""
        predictions = []

        for model_id, model in self.models.items():
            try:
                prediction = await model.predict(input_data, context)
                predictions.append(prediction)
            except Exception as e:
                logger.warning(f"⚠️ 模型 {model_id} 预测失败: {e}")

        return predictions

    async def _voting_ensemble(self, predictions: list[ModelPrediction]) -> EnsembleResult:
        """投票法集成"""
        if not predictions:
            return EnsembleResult(
                final_prediction=None,
                confidence=0.0,
                method=EnsembleMethod.VOTING,
                individual_predictions=[],
                weight_distribution={},
                improvement=0.0,
            )

        # 统计投票(简化版:假设预测是类别)
        vote_counts = defaultdict(int)
        for pred in predictions:
            vote_counts[pred.prediction] += 1

        # 选择得票最多的
        final_prediction = max(vote_counts.items(), key=lambda x: x[1])[0]

        # 计算置信度(得票比例)
        confidence = vote_counts[final_prediction] / len(predictions)

        # 均匀权重分布
        weight_dist = {pred.model_id: 1.0 / len(predictions) for pred in predictions}

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=confidence,
            method=EnsembleMethod.VOTING,
            individual_predictions=predictions,
            weight_distribution=weight_dist,
            improvement=0.0,
        )

    async def _weighted_voting_ensemble(self, predictions: list[ModelPrediction]) -> EnsembleResult:
        """加权投票法集成"""
        if not predictions:
            return EnsembleResult(
                final_prediction=None,
                confidence=0.0,
                method=EnsembleMethod.WEIGHTED_VOTING,
                individual_predictions=[],
                weight_distribution={},
                improvement=0.0,
            )

        # 获取预测对应的权重
        weights = {
            pred.model_id: self.model_weights.get(pred.model_id, 1.0) for pred in predictions
        }
        normalized_weights = normalize_dict_values(weights)

        # 加权投票
        weighted_votes = defaultdict(float)
        for pred in predictions:
            weight = normalized_weights[pred.model_id]
            weighted_votes[pred.prediction] += weight

        # 选择加权得票最多的
        final_prediction = max(weighted_votes.items(), key=lambda x: x[1])[0]
        confidence = weighted_votes[final_prediction]

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=min(1.0, confidence),
            method=EnsembleMethod.WEIGHTED_VOTING,
            individual_predictions=predictions,
            weight_distribution=normalized_weights,
            improvement=0.0,
        )

    async def _bagging_ensemble(
        self, predictions: list[ModelPrediction], input_data: dict[str, Any]
    ) -> EnsembleResult:
        """Bagging集成"""
        # 简化版:类似投票法,但考虑模型多样性
        vote_counts = defaultdict(int)

        for pred in predictions:
            # 添加置信度作为投票权重
            vote_counts[pred.prediction] += pred.confidence

        final_prediction = max(vote_counts.items(), key=lambda x: x[1])[0]
        confidence = vote_counts[final_prediction] / sum(vote_counts.values())

        # 使用工具函数归一化权重
        weight_dist = {pred.model_id: pred.confidence for pred in predictions}
        weight_dist = normalize_dict_values(weight_dist)

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=confidence,
            method=EnsembleMethod.BAGGING,
            individual_predictions=predictions,
            weight_distribution=weight_dist,
            improvement=0.0,
        )

    async def _stacking_ensemble(
        self, predictions: list[ModelPrediction], input_data: dict[str, Any]
    ) -> EnsembleResult:
        """Stacking集成"""
        # 简化版:使用元模型(基于历史表现)
        # 计算每个模型的加权得分
        scores = {}
        for pred in predictions:
            model_perf = self.models[pred.model_id].performance
            score = (
                pred.confidence * 0.5 + model_perf.accuracy * 0.3 + model_perf.success_rate * 0.2
            )
            scores[pred.prediction] = scores.get(pred.prediction, 0) + score

        final_prediction = max(scores.items(), key=lambda x: x[1])[0]
        confidence = min(1.0, scores[final_prediction] / len(predictions))

        # 使用工具函数归一化权重
        weight_dist = {
            pred.model_id: self.models[pred.model_id].performance.accuracy for pred in predictions
        }
        weight_dist = normalize_dict_values(weight_dist)

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=confidence,
            method=EnsembleMethod.STACKING,
            individual_predictions=predictions,
            weight_distribution=weight_dist,
            improvement=0.0,
        )

    async def _blending_ensemble(
        self, predictions: list[ModelPrediction], input_data: dict[str, Any]
    ) -> EnsembleResult:
        """Blending集成"""
        # 简化版:结合加权平均和置信度
        total_weight = 0
        weighted_prediction = None

        for pred in predictions:
            model_weight = self.model_weights.get(pred.model_id, 1.0)
            confidence_weight = pred.confidence
            combined_weight = model_weight * confidence_weight

            if weighted_prediction is None:
                weighted_prediction = pred.prediction * combined_weight
            else:
                weighted_prediction += pred.prediction * combined_weight

            total_weight += combined_weight

        if total_weight > 0:
            final_prediction = weighted_prediction / total_weight
        else:
            final_prediction = predictions[0].prediction if predictions else None

        confidence = statistics.mean([p.confidence for p in predictions]) if predictions else 0

        weight_dist = {
            pred.model_id: self.model_weights.get(pred.model_id, 1.0) * pred.confidence
            for pred in predictions
        }

        return EnsembleResult(
            final_prediction=final_prediction,
            confidence=confidence,
            method=EnsembleMethod.BLENDING,
            individual_predictions=predictions,
            weight_distribution=weight_dist,
            improvement=0.0,
        )

    async def _update_statistics(self, result: EnsembleResult):
        """更新统计信息"""
        # 找出最佳单个模型
        best_individual = max(
            result.individual_predictions, key=lambda p: p.confidence, default=None
        )

        # 计算改进
        if best_individual:
            improvement = result.confidence - best_individual.confidence
            result.improvement = improvement

            # 更新平均改进
            self.stats["accuracy_improvement"] = (
                self.stats["accuracy_improvement"] * (self.stats["total_ensembles"] - 1)
                + improvement
            ) / self.stats["total_ensembles"]

        # 更新平均延迟
        avg_latency = (
            statistics.mean([p.latency_ms for p in result.individual_predictions])
            if result.individual_predictions
            else 0
        )
        self.stats["avg_latency_ms"] = avg_latency

        # 更新集成准确率
        self.stats["ensemble_accuracy"] = result.confidence

        # 更新最佳模型
        if best_individual:
            self.stats["best_model"] = best_individual.model_id

    async def update_model_performance(
        self,
        model_id: str,
        accuracy: float,
        precision: float,
        recall: float,
        f1_score: float,
        latency_ms: float,
        success_rate: float,
    ):
        """
        更新模型性能

        Args:
            model_id: 模型ID
            accuracy: 准确率
            precision: 精确率
            recall: 召回率
            f1_score: F1分数
            latency_ms: 延迟
            success_rate: 成功率
        """
        if model_id not in self.models:
            logger.warning(f"⚠️ 模型 {model_id} 未注册")
            return

        model = self.models[model_id]
        total = model.performance.total_predictions

        # 更新性能指标(移动平均)
        model.performance.accuracy = (model.performance.accuracy * total + accuracy) / (total + 1)
        model.performance.precision = (model.performance.precision * total + precision) / (
            total + 1
        )
        model.performance.recall = (model.performance.recall * total + recall) / (total + 1)
        model.performance.f1_score = (model.performance.f1_score * total + f1_score) / (total + 1)
        model.performance.avg_latency_ms = (
            model.performance.avg_latency_ms * total + latency_ms
        ) / (total + 1)
        model.performance.success_rate = (model.performance.success_rate * total + success_rate) / (
            total + 1
        )
        model.performance.total_predictions += 1
        model.performance.last_updated = datetime.now()

        # 根据性能调整权重
        await self._adjust_model_weights()

        logger.debug(f"📊 模型 {model_id} 性能已更新")

    async def _adjust_model_weights(self):
        """根据性能调整模型权重"""
        total_performance = 0

        # 计算总性能
        for model_id, model in self.models.items():
            # 综合性能得分
            score = (
                model.performance.accuracy * 0.4
                + model.performance.f1_score * 0.3
                + model.performance.success_rate * 0.3
            )
            total_performance += score

        # 更新权重
        if total_performance > 0:
            for model_id, model in self.models.items():
                score = (
                    model.performance.accuracy * 0.4
                    + model.performance.f1_score * 0.3
                    + model.performance.success_rate * 0.3
                )
                self.model_weights[model_id] = score / total_performance

        logger.debug("🔄 模型权重已调整")

    def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        # 获取所有模型性能
        model_performances = []
        for model_id, model in self.models.items():
            model_performances.append(
                {
                    "model_id": model_id,
                    "accuracy": model.performance.accuracy,
                    "f1_score": model.performance.f1_score,
                    "latency_ms": model.performance.avg_latency_ms,
                    "weight": self.model_weights.get(model_id, 0),
                }
            )

        # 按权重排序
        model_performances.sort(key=lambda x: x["weight"], reverse=True)

        return {
            "name": self.name,
            "version": self.version,
            "registered_models": len(self.models),
            "default_method": self.default_method.value,
            "model_performances": model_performances,
            "statistics": self.stats,
            "recent_improvements": [
                {
                    "method": r.method.value,
                    "confidence": r.confidence,
                    "improvement": r.improvement,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.ensemble_history[-10:]
            ],
        }


# 全局单例
_ensemble_instance: MultiModelEnsemble | None = None


def get_multi_model_ensemble() -> MultiModelEnsemble:
    """获取多模型集成系统实例"""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = MultiModelEnsemble()
    return _ensemble_instance
