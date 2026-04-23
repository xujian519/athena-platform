#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强决策引擎
Enhanced Decision Engine

提供多层次的决策机制，包括深度分析、风险评估和自适应学习

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """决策类型"""
    PATENT_VALIDITY = 'patent_validity'        # 专利有效性
    PATENT_VALUE = 'patent_value'             # 专利价值
    RISK_ASSESSMENT = 'risk_assessment'       # 风险评估
    STRATEGIC_PLANNING = 'strategic_planning' # 战略规划
    RESOURCE_ALLOCATION = 'resource_allocation' # 资源分配
    CONFLICT_RESOLUTION = 'conflict_resolution' # 冲突解决

class DecisionLevel(Enum):
    """决策级别"""
    OPERATIONAL = 'operational'    # 操作级决策
    TACTICAL = 'tactical'         # 战术级决策
    STRATEGIC = 'strategic'       # 战略级决策
    CRITICAL = 'critical'         # 关键决策

class ConfidenceLevel(Enum):
    """置信度级别"""
    VERY_LOW = (0.0, 0.2)      # 极低
    LOW = (0.2, 0.4)          # 低
    MEDIUM = (0.4, 0.6)       # 中等
    HIGH = (0.6, 0.8)         # 高
    VERY_HIGH = (0.8, 1.0)    # 极高

class RiskLevel(Enum):
    """风险级别"""
    MINIMAL = 'minimal'        # 极小风险
    LOW = 'low'               # 低风险
    MODERATE = 'moderate'     # 中等风险
    HIGH = 'high'             # 高风险
    CRITICAL = 'critical'     # 严重风险

@dataclass
class DecisionFactor:
    """决策因子"""
    name: str
    weight: float
    value: float
    confidence: float
    source: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DecisionAlternative:
    """决策备选方案"""
    id: str
    name: str
    description: str
    factors: List[DecisionFactor]
    expected_outcome: Dict[str, float]
    risk_assessment: Dict[str, Any]
    implementation_cost: float
    time_to_implement: float

@dataclass
class DecisionContext:
    """决策上下文"""
    decision_type: DecisionType
    decision_level: DecisionLevel
    urgency: float  # 0-1
    available_resources: Dict[str, float]
    constraints: List[str]
    stakeholders: List[str]
    time_horizon: str  # short, medium, long
    previous_decisions: List[str]

@dataclass
class DecisionResult:
    """决策结果"""
    id: str
    decision_type: DecisionType
    selected_alternative: DecisionAlternative
    confidence_score: float
    reasoning_path: List[str]
    risk_level: RiskLevel
    expected_benefits: Dict[str, float]
    mitigation_strategies: List[str]
    monitoring_plan: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class DecisionModel:
    """决策模型基类"""

    def __init__(self, name: str):
        self.name = name
        self.is_trained = False
        self.accuracy = 0.0
        self.last_trained = None

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练模型"""
        raise NotImplementedError

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """预测"""
        raise NotImplementedError

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释预测结果"""
        raise NotImplementedError

class WeightedDecisionModel(DecisionModel):
    """加权决策模型"""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        super().__init__('WeightedDecisionModel')
        self.weights = weights or {}
        self.feature_importance = {}

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练权重"""
        if len(data) < 10:
            logger.warning('训练数据不足，使用默认权重')
            return 0.5

        # 计算每个特征的重要性
        feature_scores = defaultdict(list)
        for record in data:
            features = record.get('features', {})
            outcome = record.get('outcome', 0)

            for feature, value in features.items():
                feature_scores[feature].append(value * outcome)

        # 归一化权重
        self.feature_importance = {
            feature: np.mean(scores)
            for feature, scores in feature_scores.items()
        }

        total_importance = sum(self.feature_importance.values())
        if total_importance > 0:
            self.weights = {
                feature: score / total_importance
                for feature, score in self.feature_importance.items()
            }

        self.is_trained = True
        self.last_trained = datetime.now()

        # 计算训练准确度
        accuracy = await self._calculate_accuracy(data)
        self.accuracy = accuracy

        logger.info(f"✅ 加权决策模型训练完成，准确度: {accuracy:.2f}")
        return accuracy

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """预测决策得分"""
        features = inputs.get('features', {})

        score = 0.0
        missing_features = []

        for feature, weight in self.weights.items():
            if feature in features:
                score += features[feature] * weight
            else:
                missing_features.append(feature)

        # 标准化分数
        normalized_score = max(0, min(1, score))

        return {
            'score': normalized_score,
            'confidence': 1.0 - len(missing_features) / max(len(self.weights), 1),
            'missing_features': missing_features,
            'weights_used': self.weights
        }

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释预测结果"""
        features = inputs.get('features', {})
        explanations = []

        for feature, weight in self.weights.items():
            if feature in features:
                contribution = features[feature] * weight
                explanations.append({
                    'feature': feature,
                    'value': features[feature],
                    'weight': weight,
                    'contribution': contribution
                })

        return {
            'explanations': explanations,
            'total_contribution': sum(exp['contribution'] for exp in explanations)
        }

    async def _calculate_accuracy(self, data: List[Dict[str, Any]]) -> float:
        """计算模型准确度"""
        correct_predictions = 0
        total_predictions = len(data)

        for record in data:
            features = record.get('features', {})
            actual_outcome = record.get('outcome', 0)

            prediction = await self.predict({'features': features})
            predicted_score = prediction.get('score', 0)

            # 简单的准确度计算（基于分数阈值）
            predicted_outcome = 1 if predicted_score > 0.5 else 0
            if predicted_outcome == actual_outcome:
                correct_predictions += 1

        return correct_predictions / total_predictions if total_predictions > 0 else 0

class EnsembleDecisionModel(DecisionModel):
    """集成决策模型"""

    def __init__(self, models: List[DecisionModel]):
        super().__init__('EnsembleDecisionModel')
        self.models = models
        self.model_weights = [1.0 / len(models)] * len(models)
        self.model_performance = [0.0] * len(models)

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练集成模型"""
        # 训练各个子模型
        for i, model in enumerate(self.models):
            try:
                accuracy = await model.train(data)
                self.model_performance[i] = accuracy
                logger.info(f"📊 模型 {model.name} 训练准确度: {accuracy:.2f}")
            except Exception as e:
                logger.error(f"❌ 模型 {model.name} 训练失败: {e}")
                self.model_performance[i] = 0.0

        # 基于性能调整权重
        total_performance = sum(self.model_performance)
        if total_performance > 0:
            self.model_weights = [
                perf / total_performance
                for perf in self.model_performance
            ]

        self.is_trained = True
        self.last_trained = datetime.now()

        # 集成模型的准确度
        ensemble_accuracy = await self._calculate_ensemble_accuracy(data)
        self.accuracy = ensemble_accuracy

        logger.info(f"✅ 集成决策模型训练完成，准确度: {ensemble_accuracy:.2f}")
        return ensemble_accuracy

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """集成预测"""
        predictions = []

        for model in self.models:
            if model.is_trained:
                try:
                    prediction = await model.predict(inputs)
                    predictions.append(prediction)
                except Exception as e:
                    logger.error(f"❌ 模型 {model.name} 预测失败: {e}")

        if not predictions:
            return {'score': 0.5, 'confidence': 0.0, 'error': 'No valid predictions'}

        # 加权平均
        weighted_score = 0.0
        total_weight = 0.0

        for i, prediction in enumerate(predictions):
            weight = self.model_weights[i]
            score = prediction.get('score', 0.5)
            confidence = prediction.get('confidence', 0.5)

            # 综合考虑模型权重和预测置信度
            effective_weight = weight * confidence
            weighted_score += score * effective_weight
            total_weight += effective_weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0.5
        final_confidence = total_weight / sum(self.model_weights)

        return {
            'score': final_score,
            'confidence': final_confidence,
            'individual_predictions': predictions,
            'model_weights': self.model_weights
        }

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释集成预测"""
        explanations = []

        for i, model in enumerate(self.models):
            if model.is_trained:
                try:
                    model_explanation = await model.explain(inputs)
                    explanations.append({
                        'model_name': model.name,
                        'weight': self.model_weights[i],
                        'performance': self.model_performance[i],
                        'explanation': model_explanation
                    })
                except Exception as e:
                    logger.error(f"❌ 模型 {model.name} 解释失败: {e}")

        return {
            'ensemble_explanation': explanations,
            'total_models': len(self.models),
            'active_models': len(explanations)
        }

    async def _calculate_ensemble_accuracy(self, data: List[Dict[str, Any]]) -> float:
        """计算集成模型准确度"""
        correct_predictions = 0
        total_predictions = len(data)

        for record in data:
            features = record.get('features', {})
            actual_outcome = record.get('outcome', 0)

            prediction = await self.predict({'features': features})
            predicted_score = prediction.get('score', 0)

            predicted_outcome = 1 if predicted_score > 0.5 else 0
            if predicted_outcome == actual_outcome:
                correct_predictions += 1

        return correct_predictions / total_predictions if total_predictions > 0 else 0

class EnhancedDecisionEngine:
    """增强决策引擎"""

    def __init__(self):
        # 决策模型
        self.models: Dict[str, DecisionModel] = {}
        self.default_model = None

        # 决策历史
        self.decision_history: deque = deque(maxlen=1000)
        self.decision_performance: Dict[str, List[float]] = defaultdict(list)

        # 配置
        self.min_confidence_threshold = 0.6
        self.risk_tolerance = 0.3
        self.learning_rate = 0.01

        # 评估指标
        self.metrics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'average_confidence': 0.0,
            'average_processing_time': 0.0,
            'decision_accuracy': 0.0
        }

        # 初始化默认模型
        self._initialize_default_models()

        logger.info('🧠 增强决策引擎初始化完成')

    def _initialize_default_models(self):
        """初始化默认模型"""
        # 创建加权决策模型
        weighted_model = WeightedDecisionModel({
            'novelty': 0.25,
            'inventive': 0.25,
            'practical': 0.20,
            'commercial': 0.15,
            'legal': 0.15
        })

        self.models['weighted'] = weighted_model
        self.default_model = weighted_model

        logger.info('✅ 默认决策模型已初始化')

    def add_model(self, name: str, model: DecisionModel, set_as_default: bool = False):
        """添加决策模型"""
        self.models[name] = model
        if set_as_default or self.default_model is None:
            self.default_model = model
        logger.info(f"📝 已添加决策模型: {name}")

    async def train_models(self, training_data: List[Dict[str, Any]]):
        """训练所有模型"""
        logger.info(f"🎯 开始训练 {len(self.models)} 个模型...")

        training_results = {}

        for name, model in self.models.items():
            try:
                start_time = datetime.now()
                accuracy = await model.train(training_data)
                training_time = (datetime.now() - start_time).total_seconds()

                training_results[name] = {
                    'accuracy': accuracy,
                    'training_time': training_time,
                    'success': True
                }

                logger.info(f"✅ 模型 {name} 训练成功，准确度: {accuracy:.2f}")

            except Exception as e:
                logger.error(f"❌ 模型 {name} 训练失败: {e}")
                training_results[name] = {
                    'accuracy': 0.0,
                    'training_time': 0.0,
                    'success': False,
                    'error': str(e)
                }

        return training_results

    async def make_decision(self,
                           context: DecisionContext,
                           alternatives: List[DecisionAlternative],
                           model_name: Optional[str] = None) -> DecisionResult:
        """做出决策"""
        start_time = datetime.now()
        decision_id = str(uuid.uuid4())

        try:
            # 选择模型
            model = self.models.get(model_name, self.default_model) if model_name else self.default_model
            if not model:
                raise ValueError(f"未找到决策模型: {model_name}")

            if not model.is_trained:
                logger.warning(f"⚠️ 模型 {model.name} 未训练，使用默认权重")

            # 评估所有备选方案
            evaluated_alternatives = []
            for alternative in alternatives:
                evaluation = await self._evaluate_alternative(alternative, model, context)
                evaluated_alternatives.append((alternative, evaluation))

            # 选择最优方案
            best_alternative, best_evaluation = self._select_best_alternative(
                evaluated_alternatives, context
            )

            # 评估风险
            risk_level = self._assess_risk_level(best_evaluation)

            # 生成决策结果
            decision_result = DecisionResult(
                id=decision_id,
                decision_type=context.decision_type,
                selected_alternative=best_alternative,
                confidence_score=best_evaluation.get('confidence', 0.5),
                reasoning_path=self._generate_reasoning_path(best_alternative, best_evaluation),
                risk_level=risk_level,
                expected_benefits=best_alternative.expected_outcome,
                mitigation_strategies=self._generate_mitigation_strategies(risk_level),
                monitoring_plan=self._generate_monitoring_plan(best_alternative)
            )

            # 记录决策
            self._record_decision(decision_result, context)

            # 更新指标
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(decision_result, processing_time)

            logger.info(f"✅ 决策完成: {decision_result.id}, 置信度: {decision_result.confidence_score:.2f}")

            return decision_result

        except Exception as e:
            logger.error(f"❌ 决策失败: {e}")
            raise

    async def _evaluate_alternative(self,
                                   alternative: DecisionAlternative,
                                   model: DecisionModel,
                                   context: DecisionContext) -> Dict[str, Any]:
        """评估备选方案"""
        # 准备输入特征
        features = {
            factor.name: factor.value * factor.confidence
            for factor in alternative.factors
        }

        # 添加上下文特征
        features.update({
            'urgency': context.urgency,
            'resource_availability': sum(context.available_resources.values()) / max(len(context.available_resources), 1),
            'implementation_cost_normalized': min(alternative.implementation_cost / 1000000, 1.0),
            'time_to_implement_normalized': min(alternative.time_to_implement / 365, 1.0)
        })

        # 模型预测
        prediction = await model.predict({'features': features})

        # 获取解释
        explanation = await model.explain({'features': features})

        return {
            'score': prediction.get('score', 0.5),
            'confidence': prediction.get('confidence', 0.5),
            'features': features,
            'prediction': prediction,
            'explanation': explanation
        }

    def _select_best_alternative(self,
                                evaluated_alternatives: List[Tuple[DecisionAlternative, Dict[str, Any]]],
                                context: DecisionContext) -> Tuple[DecisionAlternative, Dict[str, Any]]:
        """选择最优备选方案"""
        if not evaluated_alternatives:
            raise ValueError('没有可用的备选方案')

        # 根据决策类型和紧急程度调整选择策略
        if context.urgency > 0.8:
            # 高紧急情况：选择实现时间最短的
            best = min(evaluated_alternatives, key=lambda x: x[0].time_to_implement)
        elif context.decision_level == DecisionLevel.STRATEGIC:
            # 战略决策：选择综合得分最高的
            best = max(evaluated_alternatives, key=lambda x: x[1]['score'])
        else:
            # 默认：平衡得分和置信度
            best = max(
                evaluated_alternatives,
                key=lambda x: x[1]['score'] * x[1]['confidence']
            )

        return best

    def _assess_risk_level(self, evaluation: Dict[str, Any]) -> RiskLevel:
        """评估风险级别"""
        score = evaluation.get('score', 0.5)
        confidence = evaluation.get('confidence', 0.5)

        # 综合风险分数（分数越低或置信度越低，风险越高）
        risk_score = 1 - (score * confidence)

        if risk_score > 0.8:
            return RiskLevel.CRITICAL
        elif risk_score > 0.6:
            return RiskLevel.HIGH
        elif risk_score > 0.4:
            return RiskLevel.MODERATE
        elif risk_score > 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    def _generate_reasoning_path(self,
                                alternative: DecisionAlternative,
                                evaluation: Dict[str, Any]) -> List[str]:
        """生成推理路径"""
        reasoning = [
            f"分析备选方案: {alternative.name}",
            f"计算综合得分: {evaluation['score']:.2f}",
            f"评估置信度: {evaluation['confidence']:.2f}"
        ]

        # 添加关键因子说明
        explanations = evaluation.get('explanation', {}).get('explanations', [])
        if explanations:
            top_factors = sorted(explanations, key=lambda x: abs(x['contribution']), reverse=True)[:3]
            for factor in top_factors:
                reasoning.append(
                    f"关键因子 {factor['feature']}: 贡献值 {factor['contribution']:.2f}"
                )

        reasoning.append(f"最终选择: {alternative.name}")

        return reasoning

    def _generate_mitigation_strategies(self, risk_level: RiskLevel) -> List[str]:
        """生成风险缓解策略"""
        strategies = {
            RiskLevel.MINIMAL: [
                '定期监控决策效果',
                '保持现状'
            ],
            RiskLevel.LOW: [
                '制定应急预案',
                '加强过程监控',
                '定期评估效果'
            ],
            RiskLevel.MODERATE: [
                '实施阶段性检查点',
                '准备备选方案',
                '增强监控频率'
            ],
            RiskLevel.HIGH: [
                '分阶段实施',
                '持续风险评估',
                '建立快速响应机制'
            ],
            RiskLevel.CRITICAL: [
                '实施前进行全面测试',
                '建立多重保障机制',
                '设置实时监控和告警'
            ]
        }

        return strategies.get(risk_level, strategies[RiskLevel.MODERATE])

    def _generate_monitoring_plan(self, alternative: DecisionAlternative) -> List[str]:
        """生成监控计划"""
        return [
            f"监控关键指标: {list(alternative.expected_outcome.keys())}",
            f"跟踪实施进度，预期时间: {alternative.time_to_implement}天",
            '定期评估实际效果与预期差异',
            '收集相关方反馈',
            '调整优化方案参数'
        ]

    def _record_decision(self, decision: DecisionResult, context: DecisionContext):
        """记录决策"""
        self.decision_history.append({
            'decision': decision,
            'context': context,
            'timestamp': datetime.now()
        })

        # 记录决策类型的表现
        decision_type = decision.decision_type.value
        self.decision_performance[decision_type].append(decision.confidence_score)

        # 限制历史记录长度
        if len(self.decision_performance[decision_type]) > 100:
            self.decision_performance[decision_type] = self.decision_performance[decision_type][-100:]

    def _update_metrics(self, decision: DecisionResult, processing_time: float):
        """更新指标"""
        self.metrics['total_decisions'] += 1

        # 更新平均置信度
        current_avg = self.metrics['average_confidence']
        total = self.metrics['total_decisions']
        self.metrics['average_confidence'] = (
            (current_avg * (total - 1) + decision.confidence_score) / total
        )

        # 更新平均处理时间
        current_time_avg = self.metrics['average_processing_time']
        self.metrics['average_processing_time'] = (
            (current_time_avg * (total - 1) + processing_time) / total
        )

        # 更新成功决策数（基于置信度）
        if decision.confidence_score >= self.min_confidence_threshold:
            self.metrics['successful_decisions'] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {
            'metrics': self.metrics.copy(),
            'models': {
                name: {
                    'is_trained': model.is_trained,
                    'accuracy': model.accuracy,
                    'last_trained': model.last_trained.isoformat() if model.last_trained else None
                }
                for name, model in self.models.items()
            },
            'decision_type_performance': {}
        }

        # 计算各决策类型的平均表现
        for decision_type, scores in self.decision_performance.items():
            if scores:
                report['decision_type_performance'][decision_type] = {
                    'average_confidence': np.mean(scores),
                    'count': len(scores),
                    'trend': 'improving' if len(scores) > 1 and scores[-1] > np.mean(scores[:-1]) else 'stable'
                }

        return report

    def export_decisions(self, file_path: str, limit: Optional[int] = None):
        """导出决策历史"""
        decisions_to_export = list(self.decision_history)[-limit:] if limit else list(self.decision_history)

        exported_data = []
        for record in decisions_to_export:
            decision = record['decision']
            context = record['context']

            exported_data.append({
                'decision_id': decision.id,
                'decision_type': decision.decision_type.value,
                'selected_alternative': decision.selected_alternative.name,
                'confidence_score': decision.confidence_score,
                'risk_level': decision.risk_level.value,
                'expected_benefits': decision.expected_outcome,
                'reasoning_path': decision.reasoning_path,
                'timestamp': decision.timestamp.isoformat(),
                'context': {
                    'decision_level': context.decision_level.value,
                    'urgency': context.urgency,
                    'time_horizon': context.time_horizon
                }
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 决策历史已导出到: {file_path}，共 {len(exported_data)} 条记录")

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 增强决策引擎测试')
    logger.info(str('='*50))

    # 创建决策引擎
    engine = EnhancedDecisionEngine()

    # 创建测试备选方案
    alternatives = [
        DecisionAlternative(
            id='alt1',
            name='方案A: 授权专利',
            description='完全授权专利申请',
            factors=[
                DecisionFactor('novelty', 0.8, 0.85, 0.9, 'technical_analysis'),
                DecisionFactor('inventive', 0.75, 0.78, 0.85, 'expert_review'),
                DecisionFactor('practical', 0.9, 0.92, 0.95, 'market_analysis')
            ],
            expected_outcome={
                'legal_protection': 0.9,
                'commercial_value': 0.8,
                'innovation_recognition': 0.85
            },
            risk_assessment={
                'infringement_risk': 0.1,
                'invalidation_risk': 0.2
            },
            implementation_cost=50000,
            time_to_implement=30
        ),
        DecisionAlternative(
            id='alt2',
            name='方案B: 部分授权',
            description='部分授权专利申请',
            factors=[
                DecisionFactor('novelty', 0.7, 0.72, 0.8, 'technical_analysis'),
                DecisionFactor('inventive', 0.65, 0.68, 0.75, 'expert_review'),
                DecisionFactor('practical', 0.85, 0.88, 0.9, 'market_analysis')
            ],
            expected_outcome={
                'legal_protection': 0.7,
                'commercial_value': 0.6,
                'innovation_recognition': 0.65
            },
            risk_assessment={
                'infringement_risk': 0.05,
                'invalidation_risk': 0.15
            },
            implementation_cost=30000,
            time_to_implement=20
        )
    ]

    # 创建决策上下文
    context = DecisionContext(
        decision_type=DecisionType.PATENT_VALIDITY,
        decision_level=DecisionLevel.TACTICAL,
        urgency=0.7,
        available_resources={
            'budget': 100000,
            'personnel': 5,
            'time': 60
        },
        constraints=['需要快速决策', '预算有限'],
        stakeholders=['专利申请人', '审查员', '技术专家'],
        time_horizon='medium',
        previous_decisions=[]
    )

    # 训练模型（使用模拟数据）
    logger.info("\n🎯 训练决策模型...")
    training_data = [
        {
            'features': {
                'novelty': 0.8,
                'inventive': 0.7,
                'practical': 0.9,
                'commercial': 0.6,
                'legal': 0.8
            },
            'outcome': 1
        },
        {
            'features': {
                'novelty': 0.4,
                'inventive': 0.3,
                'practical': 0.7,
                'commercial': 0.5,
                'legal': 0.6
            },
            'outcome': 0
        }
    ]

    training_results = await engine.train_models(training_data)
    logger.info(f"训练结果: {json.dumps(training_results, indent=2, ensure_ascii=False)}")

    # 执行决策
    logger.info("\n🤔 执行决策...")
    decision = await engine.make_decision(context, alternatives)

    logger.info(f"\n✅ 决策结果:")
    logger.info(f"决策ID: {decision.id}")
    logger.info(f"选择的方案: {decision.selected_alternative.name}")
    logger.info(f"置信度: {decision.confidence_score:.2f}")
    logger.info(f"风险级别: {decision.risk_level.value}")
    logger.info(f"\n推理路径:")
    for i, step in enumerate(decision.reasoning_path, 1):
        logger.info(f"  {i}. {step}")

    logger.info(f"\n预期收益:")
    for benefit, value in decision.expected_benefits.items():
        logger.info(f"  - {benefit}: {value:.2f}")

    logger.info(f"\n缓解策略:")
    for strategy in decision.mitigation_strategies:
        logger.info(f"  - {strategy}")

    # 获取性能报告
    logger.info("\n📊 性能报告:")
    performance = engine.get_performance_report()
    print(json.dumps(performance, indent=2, ensure_ascii=False))

    # 导出决策历史
    engine.export_decisions('decision_history.json')
    logger.info("\n✅ 决策历史已导出")

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())