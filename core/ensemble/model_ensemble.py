#!/usr/bin/env python3
from __future__ import annotations
"""
多模型集成系统 - 第二阶段
Multi-Model Ensemble System - Phase 2

核心功能:
1. 模型权重管理
2. 投票/堆叠/混合集成
3. 动态权重调整
4. 集成性能评估

作者: 小诺·双鱼公主
版本: v1.0.0 "模型集成"
创建: 2026-01-12
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EnsembleMethod(Enum):
    """集成方法"""

    VOTING = "voting"  # 投票法
    STACKING = "stacking"  # 堆叠法
    BLENDING = "blending"  # 混合法
    WEIGHTED_AVG = "weighted_avg"  # 加权平均
    DYNAMIC = "dynamic"  # 动态集成


@dataclass
class ModelPrediction:
    """模型预测结果"""

    model_id: str
    prediction: Any  # 预测结果
    confidence: float  # 置信度
    metadata: dict[str, Any]  # 元数据
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnsembleResult:
    """集成结果"""

    final_prediction: Any
    confidence: float
    method: EnsembleMethod
    model_contributions: dict[str, float]  # 各模型贡献度
    individual_predictions: list[ModelPrediction]
    reasoning: str


@dataclass
class EnsembleConfig:
    """集成配置"""

    ensemble_id: str
    method: EnsembleMethod
    models: list[str]  # 参与集成的模型
    weights: dict[str, float]  # 模型权重
    voting_strategy: str = "soft"  # hard/soft voting
    threshold: float = 0.5  # 决策阈值


class ModelEnsemble:
    """模型集成器"""

    def __init__(self):
        self.name = "多模型集成系统 v1.0"
        self.version = "1.0.0"

        # 模型注册表
        self.model_registry: dict[str, Any] = {}

        # 集成配置
        self.ensembles: dict[str, EnsembleConfig] = {}

        # 性能历史
        self.performance_history: dict[str, list[float]] = {}

        # 动态权重
        self.dynamic_weights: dict[str, dict[str, float]] = {}

        logger.info(f"🔮 {self.name} 初始化完成")

    def register_model(self, model_id: str, model: Any, model_type: str):
        """注册模型"""
        self.model_registry[model_id] = {
            "model": model,
            "type": model_type,
            "registered_at": datetime.now(),
        }
        logger.info(f"✅ 模型已注册: {model_id} ({model_type})")

    def create_ensemble(
        self,
        ensemble_id: str,
        method: EnsembleMethod,
        models: list[str],
        weights: dict[str, float] | None = None,
        **kwargs,
    ) -> EnsembleConfig:
        """创建集成配置"""
        # 验证模型存在
        for model_id in models:
            if model_id not in self.model_registry:
                raise ValueError(f"模型不存在: {model_id}")

        # 默认权重(均等)
        if weights is None:
            weights = {m: 1.0 / len(models) for m in models}

        # 归一化权重
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        config = EnsembleConfig(
            ensemble_id=ensemble_id, method=method, models=models, weights=weights, **kwargs
        )

        self.ensembles[ensemble_id] = config
        logger.info(f"✅ 集成配置已创建: {ensemble_id} ({method.value})")

        return config

    async def predict(
        self, ensemble_id: str, input_data: Any, context: Optional[dict[str, Any]] = None
    ) -> EnsembleResult:
        """
        执行集成预测

        Args:
            ensemble_id: 集成ID
            input_data: 输入数据
            context: 上下文信息

        Returns:
            EnsembleResult: 集成结果
        """
        if ensemble_id not in self.ensembles:
            raise ValueError(f"集成配置不存在: {ensemble_id}")

        config = self.ensembles[ensemble_id]

        # 1. 获取各模型预测
        individual_predictions = []
        for model_id in config.models:
            pred = await self._get_model_prediction(model_id, input_data, context)
            individual_predictions.append(pred)

        # 2. 根据集成方法组合结果
        if config.method == EnsembleMethod.VOTING:
            result = self._voting_ensemble(individual_predictions, config)
        elif config.method == EnsembleMethod.STACKING:
            result = self._stacking_ensemble(individual_predictions, config)
        elif config.method == EnsembleMethod.BLENDING:
            result = self._blending_ensemble(individual_predictions, config)
        elif config.method == EnsembleMethod.WEIGHTED_AVG:
            result = self._weighted_average_ensemble(individual_predictions, config)
        elif config.method == EnsembleMethod.DYNAMIC:
            result = self._dynamic_ensemble(individual_predictions, config)
        else:
            raise ValueError(f"未知集成方法: {config.method}")

        # 3. 计算模型贡献度
        contributions = self._calculate_contributions(individual_predictions, result)

        return EnsembleResult(
            final_prediction=result.final_prediction,
            confidence=result.confidence,
            method=config.method,
            model_contributions=contributions,
            individual_predictions=individual_predictions,
            reasoning=result.reasoning,
        )

    async def _get_model_prediction(
        self, model_id: str, input_data: Any, context: dict[str, Any]
    ) -> ModelPrediction:
        """获取模型预测"""
        # 简化实现: 模拟模型预测
        # 实际应该调用真实模型

        # 模拟不同模型的预测
        if "bert" in model_id.lower():
            prediction = {"intent": "patent_search", "confidence": 0.92}
        elif "bge" in model_id.lower():
            prediction = {"intent": "patent_search", "confidence": 0.95}
        elif "rules" in model_id.lower():
            prediction = {"intent": "patent_search", "confidence": 0.88}
        else:
            prediction = {"intent": "daily_chat", "confidence": 0.80}

        return ModelPrediction(
            model_id=model_id,
            prediction=prediction,
            confidence=prediction.get("confidence", 0.8),
            metadata={"model_type": "classification"},
        )

    def _voting_ensemble(
        self, predictions: list[ModelPrediction], config: EnsembleConfig
    ) -> EnsembleResult:
        """投票集成"""
        if config.voting_strategy == "hard":
            # 硬投票: 多数表决
            votes = {}
            for pred in predictions:
                pred_label = pred.prediction.get("intent", "unknown")
                votes[pred_label] = votes.get(pred_label, 0) + 1

            final_pred = max(votes.items(), key=lambda x: x[1])[0]
            confidence = votes[final_pred] / len(predictions)

            return EnsembleResult(
                final_prediction={"intent": final_pred},
                confidence=confidence,
                method=config.method,
                model_contributions={},
                individual_predictions=predictions,
                reasoning=f"硬投票: {votes}",
            )

        else:
            # 软投票: 加权平均置信度
            intent_scores = {}

            for pred in predictions:
                pred_label = pred.prediction.get("intent", "unknown")
                weight = config.weights.get(pred.model_id, 1.0)
                weighted_conf = pred.confidence * weight

                if pred_label not in intent_scores:
                    intent_scores[pred_label] = 0.0
                intent_scores[pred_label] += weighted_conf

            # 归一化
            total_weight = sum(config.weights.values())
            intent_scores = {k: v / total_weight for k, v in intent_scores.items()}

            final_pred = max(intent_scores.items(), key=lambda x: x[1])[0]
            confidence = intent_scores[final_pred]

            return EnsembleResult(
                final_prediction={"intent": final_pred},
                confidence=confidence,
                method=config.method,
                model_contributions={},
                individual_predictions=predictions,
                reasoning=f"软投票: {intent_scores}",
            )

    def _stacking_ensemble(
        self, predictions: list[ModelPrediction], config: EnsembleConfig
    ) -> EnsembleResult:
        """堆叠集成"""
        # 简化实现: 使用元模型
        # 实际应该训练一个元模型

        # 计算加权得分
        total_score = 0.0
        for pred in predictions:
            weight = config.weights.get(pred.model_id, 1.0)
            score = pred.confidence * weight
            total_score += score

        final_pred = predictions[0].prediction  # 使用第一个模型的预测结构
        confidence = total_score / sum(config.weights.values())

        return EnsembleResult(
            final_prediction=final_pred,
            confidence=confidence,
            method=config.method,
            model_contributions={},
            individual_predictions=predictions,
            reasoning=f"堆叠集成: 总分={total_score:.3f}",
        )

    def _blending_ensemble(
        self, predictions: list[ModelPrediction], config: EnsembleConfig
    ) -> EnsembleResult:
        """混合集成"""
        # 结合多个策略的结果
        voting_result = self._voting_ensemble(predictions, config)
        weighted_result = self._weighted_average_ensemble(predictions, config)

        # 混合置信度
        blended_confidence = voting_result.confidence * 0.6 + weighted_result.confidence * 0.4

        return EnsembleResult(
            final_prediction=voting_result.final_prediction,
            confidence=blended_confidence,
            method=config.method,
            model_contributions={},
            individual_predictions=predictions,
            reasoning=f"混合集成: 投票({voting_result.confidence:.2f}) + 加权({weighted_result.confidence:.2f})",
        )

    def _weighted_average_ensemble(
        self, predictions: list[ModelPrediction], config: EnsembleConfig
    ) -> EnsembleResult:
        """加权平均集成"""
        # 加权平均置信度
        total_weight = 0.0
        weighted_confidence = 0.0

        for pred in predictions:
            weight = config.weights.get(pred.model_id, 1.0)
            weighted_confidence += pred.confidence * weight
            total_weight += weight

        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0

        # 使用最高置信度的预测
        best_pred = max(predictions, key=lambda p: p.confidence)

        return EnsembleResult(
            final_prediction=best_pred.prediction,
            confidence=final_confidence,
            method=config.method,
            model_contributions={},
            individual_predictions=predictions,
            reasoning=f"加权平均: {final_confidence:.3f}",
        )

    def _dynamic_ensemble(
        self, predictions: list[ModelPrediction], config: EnsembleConfig
    ) -> EnsembleResult:
        """动态集成"""
        # 基于历史性能动态调整权重
        ensemble_id = config.ensemble_id

        if ensemble_id not in self.dynamic_weights:
            self.dynamic_weights[ensemble_id] = config.weights.copy()

        # 获取动态权重
        dynamic_weights = self._get_dynamic_weights(ensemble_id, predictions)

        # 使用动态权重进行加权平均
        total_weight = 0.0
        weighted_confidence = 0.0

        for pred in predictions:
            weight = dynamic_weights.get(pred.model_id, 1.0)
            weighted_confidence += pred.confidence * weight
            total_weight += weight

        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
        best_pred = max(predictions, key=lambda p: p.confidence)

        return EnsembleResult(
            final_prediction=best_pred.prediction,
            confidence=final_confidence,
            method=config.method,
            model_contributions=dynamic_weights,
            individual_predictions=predictions,
            reasoning=f"动态集成: 权重={dynamic_weights}",
        )

    def _get_dynamic_weights(
        self, ensemble_id: str, predictions: list[ModelPrediction]
    ) -> dict[str, float]:
        """获取动态权重"""
        # 基于历史性能调整权重
        base_weights = self.ensembles[ensemble_id].weights
        dynamic_weights = base_weights.copy()

        # 简化实现: 如果有历史性能数据,根据性能调整权重
        for model_id in dynamic_weights:
            if model_id in self.performance_history:
                recent_perf = self.performance_history[model_id][-10:]
                avg_perf = sum(recent_perf) / len(recent_perf)

                # 性能好的模型增加权重
                if avg_perf > 0.9:
                    dynamic_weights[model_id] *= 1.2
                elif avg_perf < 0.7:
                    dynamic_weights[model_id] *= 0.8

        # 归一化
        total = sum(dynamic_weights.values())
        dynamic_weights = {k: v / total for k, v in dynamic_weights.items()}

        return dynamic_weights

    def _calculate_contributions(
        self, predictions: list[ModelPrediction], result: EnsembleResult
    ) -> dict[str, float]:
        """计算模型贡献度"""
        contributions = {}

        for pred in predictions:
            # 简化计算: 基于置信度和最终结果的相似度
            contribution = pred.confidence * result.confidence
            contributions[pred.model_id] = contribution

        # 归一化
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: v / total for k, v in contributions.items()}

        return contributions

    def update_model_performance(self, model_id: str, performance: float):
        """更新模型性能"""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = []

        self.performance_history[model_id].append(performance)

        # 限制历史长度
        if len(self.performance_history[model_id]) > 100:
            self.performance_history[model_id] = self.performance_history[model_id][-50:]

    def get_ensemble_stats(self) -> dict[str, Any]:
        """获取集成统计"""
        return {
            "registered_models": len(self.model_registry),
            "active_ensembles": len(self.ensembles),
            "models_with_performance": len(self.performance_history),
            "dynamic_weights_updated": len(self.dynamic_weights),
        }


# 全局实例
_ensemble_instance: ModelEnsemble | None = None


def get_model_ensemble() -> ModelEnsemble:
    """获取模型集成器单例"""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = ModelEnsemble()
    return _ensemble_instance
