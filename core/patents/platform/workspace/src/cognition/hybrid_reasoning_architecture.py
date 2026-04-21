#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合推理架构
Hybrid Reasoning Architecture

规则推理与神经网络的深度结合架构

作者: Athena + 小诺
创建时间: 2025-12-05
版本: 3.0.0
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from cognitive_decision_manager import CognitiveDecisionManager, DecisionMetrics

# 导入现有模块
from enhanced_reasoning_engine import (
    EnhancedReasoningEngine,
    LegalRule,
    ReasoningResult,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReasoningMode(Enum):
    """推理模式"""
    RULE_ONLY = 'rule_only'                    # 纯规则推理
    NEURAL_ONLY = 'neural_only'                # 纯神经网络推理
    HYBRID_SEQUENTIAL = 'hybrid_sequential'    # 顺序混合推理
    HYBRID_PARALLEL = 'hybrid_parallel'        # 并行混合推理
    ADAPTIVE = 'adaptive'                      # 自适应混合推理

class FusionStrategy(Enum):
    """融合策略"""
    WEIGHTED_AVERAGE = 'weighted_average'      # 加权平均
    ATTENTION_FUSION = 'attention_fusion'      # 注意力融合
    ENSEMBLE_VOTING = 'ensemble_voting'        # 集成投票
    META_LEARNING = 'meta_learning'            # 元学习融合

@dataclass
class NeuralInput:
    """神经网络输入"""
    patent_features: np.ndarray
    rule_activations: np.ndarray
    context_embeddings: np.ndarray
    domain_indicators: np.ndarray

@dataclass
class HybridReasoningResult:
    """混合推理结果"""
    conclusion: str
    confidence: float
    rule_contribution: float
    neural_contribution: float
    fusion_score: float
    reasoning_path: List[str]
    ensemble_decisions: Dict[str, float]
    meta_features: Dict[str, Any]
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)

class PatentNeuralNetwork(nn.Module):
    """专利分析神经网络"""

    def __init__(self,
                 input_dim: int = 512,
                 hidden_dims: List[int] = [256, 128, 64],
                 output_dim: int = 32,
                 dropout_rate: float = 0.2):
        super(PatentNeuralNetwork, self).__init__()

        self.input_dim = input_dim
        self.output_dim = output_dim

        # 特征提取层
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim

        self.feature_extractor = nn.Sequential(*layers)

        # 专利属性预测头
        self.novelty_head = nn.Sequential(
            nn.Linear(prev_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        self.inventive_head = nn.Sequential(
            nn.Linear(prev_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        self.practical_head = nn.Sequential(
            nn.Linear(prev_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        # 决策置信度预测头
        self.confidence_head = nn.Sequential(
            nn.Linear(prev_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

        # 注意力机制
        self.attention = nn.MultiheadAttention(
            embed_dim=prev_dim,
            num_heads=8,
            dropout=dropout_rate
        )

        # 融合层
        self.fusion_layer = nn.Sequential(
            nn.Linear(prev_dim * 3, 128),  # 规则+神经网络+上下文
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self,
                patent_features: torch.Tensor,
                rule_features: torch.Tensor,
                context_features: torch.Tensor) -> Dict[str, torch.Tensor]:

        # 特征提取
        patent_repr = self.feature_extractor(patent_features)
        rule_repr = self.feature_extractor(rule_features)
        context_repr = self.feature_extractor(context_features)

        # 注意力融合
        combined_features = torch.stack([patent_repr, rule_repr, context_repr], dim=1)
        attended_features, attention_weights = self.attention(
            combined_features, combined_features, combined_features
        )

        # 分别预测各个属性
        novelty_score = self.novelty_head(patent_repr)
        inventive_score = self.inventive_head(patent_repr)
        practical_score = self.practical_head(patent_repr)
        confidence_score = self.confidence_head(patent_repr)

        # 最终融合
        fused_features = torch.cat([
            attended_features.mean(dim=1),
            patent_repr,
            rule_repr
        ], dim=1)

        final_output = self.fusion_layer(fused_features)

        return {
            'novelty': novelty_score,
            'inventive': inventive_score,
            'practical': practical_score,
            'confidence': confidence_score,
            'final_embedding': final_output,
            'attention_weights': attention_weights
        }

class AttentionFusion(nn.Module):
    """注意力融合模块"""

    def __init__(self, feature_dims: List[int], output_dim: int = 64):
        super(AttentionFusion, self).__init__()

        self.feature_dims = feature_dims
        self.output_dim = output_dim

        # 为每种特征类型创建投影层
        self.projections = nn.ModuleList([
            nn.Linear(dim, output_dim) for dim in feature_dims
        ])

        # 注意力权重计算
        self.attention_weights = nn.Sequential(
            nn.Linear(output_dim * len(feature_dims), output_dim),
            nn.Tanh(),
            nn.Linear(output_dim, len(feature_dims)),
            nn.Softmax(dim=-1)
        )

    def forward(self, features: List[torch.Tensor]) -> torch.Tensor:
        # 投影到统一维度
        projected_features = []
        for i, (feature, projection) in enumerate(zip(features, self.projections)):
            projected = projection(feature)
            projected_features.append(projected)

        # 拼接特征
        concatenated = torch.cat(projected_features, dim=-1)

        # 计算注意力权重
        weights = self.attention_weights(concatenated)

        # 加权融合
        weighted_features = []
        for i, projected in enumerate(projected_features):
            weight = weights[:, i:i+1]  # 保持维度
            weighted_features.append(projected * weight)

        # 求和得到最终融合特征
        fused_feature = torch.stack(weighted_features, dim=0).sum(dim=0)

        return fused_feature

class MetaLearningNetwork(nn.Module):
    """元学习网络"""

    def __init__(self, input_dim: int = 128, hidden_dim: int = 64):
        super(MetaLearningNetwork, self).__init__()

        # 元特征提取
        self.meta_extractor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # 权重生成器
        self.rule_weight_gen = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

        self.neural_weight_gen = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

        # 质量评估器
        self.quality_assessor = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self,
                combined_features: torch.Tensor,
                rule_output: torch.Tensor,
                neural_output: torch.Tensor) -> Dict[str, torch.Tensor]:

        meta_features = self.meta_extractor(combined_features)

        # 生成动态权重
        rule_weight = self.rule_weight_gen(meta_features)
        neural_weight = self.neural_weight_gen(meta_features)

        # 归一化权重
        total_weight = rule_weight + neural_weight + 1e-8
        rule_weight = rule_weight / total_weight
        neural_weight = neural_weight / total_weight

        # 质量评估
        quality_score = self.quality_assessor(meta_features)

        return {
            'rule_weight': rule_weight,
            'neural_weight': neural_weight,
            'quality_score': quality_score
        }

class HybridReasoningEngine:
    """混合推理引擎"""

    def __init__(self):
        # 初始化组件
        self.rule_engine = EnhancedReasoningEngine()
        self.cognitive_manager = CognitiveDecisionManager()

        # 初始化神经网络
        self.neural_network = PatentNeuralNetwork()
        self.attention_fusion = AttentionFusion([512, 256, 128])
        self.meta_learner = MetaLearningNetwork()

        # 推理配置
        self.reasoning_mode = ReasoningMode.ADAPTIVE
        self.fusion_strategy = FusionStrategy.ATTENTION_FUSION

        # 性能监控
        self.performance_metrics = {
            'total_reasonings': 0,
            'mode_usage': {mode.value: 0 for mode in ReasoningMode},
            'fusion_accuracy': 0.0,
            'average_confidence': 0.0
        }

        # 学习历史
        self.learning_history = []
        self.fusion_weights_history = []

    async def hybrid_reason(self,
                           patent_data: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> HybridReasoningResult:
        """执行混合推理"""
        start_time = datetime.now()
        logger.info(f"🧠 开始混合推理分析: {patent_data.get('patent_id', 'unknown')}")

        try:
            context = context or {}

            # 1. 规则推理
            rule_result = await self._rule_reasoning(patent_data, context)

            # 2. 神经网络推理
            neural_result = await self._neural_reasoning(patent_data, context, rule_result)

            # 3. 自适应推理模式选择
            reasoning_mode = self._select_reasoning_mode(patent_data, rule_result, neural_result)

            # 4. 混合推理执行
            hybrid_result = await self._execute_hybrid_reasoning(
                reasoning_mode, patent_data, context, rule_result, neural_result
            )

            # 5. 性能评估和学习
            await self._evaluate_and_learn(patent_data, rule_result, neural_result, hybrid_result)

            # 6. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            hybrid_result.processing_time = processing_time

            # 7. 更新性能指标
            self._update_performance_metrics(reasoning_mode, hybrid_result)

            logger.info(f"✅ 混合推理完成，模式: {reasoning_mode.value}，置信度: {hybrid_result.confidence:.2f}")
            return hybrid_result

        except Exception as e:
            logger.error(f"❌ 混合推理失败: {e}")
            raise

    async def _rule_reasoning(self, patent_data: Dict[str, Any], context: Dict[str, Any]) -> ReasoningResult:
        """规则推理"""
        return await self.rule_engine.reason(patent_data, context)

    async def _neural_reasoning(self,
                               patent_data: Dict[str, Any],
                               context: Dict[str, Any],
                               rule_result: ReasoningResult) -> Dict[str, Any]:
        """神经网络推理"""
        # 准备输入数据
        neural_input = self._prepare_neural_input(patent_data, context, rule_result)

        # 转换为张量
        patent_features = torch.FloatTensor(neural_input.patent_features).unsqueeze(0)
        rule_features = torch.FloatTensor(neural_input.rule_activations).unsqueeze(0)
        context_features = torch.FloatTensor(neural_input.context_embeddings).unsqueeze(0)

        # 神经网络前向传播
        with torch.no_grad():
            neural_output = self.neural_network(
                patent_features, rule_features, context_features
            )

        return {
            'novelty_score': neural_output['novelty'].item(),
            'inventive_score': neural_output['inventive'].item(),
            'practical_score': neural_output['practical'].item(),
            'confidence_score': neural_output['confidence'].item(),
            'final_embedding': neural_output['final_embedding'].numpy().flatten(),
            'attention_weights': neural_output['attention_weights'].numpy()
        }

    def _prepare_neural_input(self,
                             patent_data: Dict[str, Any],
                             context: Dict[str, Any],
                             rule_result: ReasoningResult) -> NeuralInput:
        """准备神经网络输入"""
        # 专利特征向量（简化版本）
        patent_features = np.array([
            patent_data.get('novelty_score', 0.5),
            patent_data.get('inventive_score', 0.5),
            patent_data.get('practical_score', 0.5),
            len(patent_data.get('title', '')),
            len(patent_data.get('abstract', '')),
            len(patent_data.get('claims', '')),
            hash(patent_data.get('technical_field', '')) % 100 / 100.0
        ])

        # 规则激活向量
        rule_activations = np.array([
            rule_result.confidence,
            len(rule_result.applied_rules) / 10.0,  # 归一化
            len(rule_result.conflicts_detected) / 5.0,
            1.0 if rule_result.resolution_strategy == 'priority_based' else 0.0
        ])

        # 上下文嵌入向量
        context_embeddings = np.array([
            context.get('urgency_level', 0.5),
            context.get('complexity_score', 0.5),
            len(context.get('related_patents', [])) / 20.0,
            1.0 if context.get('expedited_review', False) else 0.0
        ])

        # 扩展到标准维度
        patent_features = np.pad(patent_features, (0, 512 - len(patent_features)), 'constant')
        rule_activations = np.pad(rule_activations, (0, 256 - len(rule_activations)), 'constant')
        context_embeddings = np.pad(context_embeddings, (0, 128 - len(context_embeddings)), 'constant')

        return NeuralInput(
            patent_features=patent_features,
            rule_activations=rule_activations,
            context_embeddings=context_embeddings,
            domain_indicators=zeros(8)  # 8个领域的one-hot编码
        , dtype=np.float64)

    def _select_reasoning_mode(self,
                              patent_data: Dict[str, Any],
                              rule_result: ReasoningResult,
                              neural_result: Dict[str, Any]) -> ReasoningMode:
        """自适应选择推理模式"""

        # 基于多个因素选择模式
        factors = {
            'rule_confidence': rule_result.confidence,
            'neural_confidence': neural_result['confidence_score'],
            'rule_conflicts': len(rule_result.conflicts_detected),
            'data_complexity': self._assess_data_complexity(patent_data),
            'domain_specificity': self._assess_domain_specificity(patent_data)
        }

        # 决策逻辑
        if factors['rule_confidence'] > 0.9 and factors['rule_conflicts'] == 0:
            return ReasoningMode.RULE_ONLY

        elif factors['neural_confidence'] > 0.9 and factors['data_complexity'] > 0.7:
            return ReasoningMode.NEURAL_ONLY

        elif factors['rule_conflicts'] > 2 or factors['data_complexity'] > 0.8:
            return ReasoningMode.HYBRID_PARALLEL

        else:
            return ReasoningMode.HYBRID_SEQUENTIAL

    def _assess_data_complexity(self, patent_data: Dict[str, Any]) -> float:
        """评估数据复杂度"""
        complexity_indicators = [
            len(patent_data.get('title', '')),
            len(patent_data.get('abstract', '')),
            len(patent_data.get('claims', '')),
            len(patent_data.get('description', '')),
            len(patent_data.get('keywords', [])),
        ]

        # 归一化复杂度分数
        max_complexity = 10000  # 假设的最大复杂度
        current_complexity = sum(complexity_indicators)

        return min(current_complexity / max_complexity, 1.0)

    def _assess_domain_specificity(self, patent_data: Dict[str, Any]) -> float:
        """评估领域特异性"""
        domain_keywords = {
            'software': ['algorithm', 'software', 'computer', 'digital', 'program'],
            'mechanical': ['machine', 'mechanical', 'device', 'structure', 'apparatus'],
            'electrical': ['circuit', 'electrical', 'voltage', 'current', 'electronic'],
            'chemical': ['compound', 'chemical', 'reaction', 'molecule', 'composition']
        }

        text = f"{patent_data.get('title', '')} {patent_data.get('abstract', '')}".lower()

        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            domain_scores[domain] = score / len(keywords)

        # 如果有明显的领域倾向，特异性高
        max_score = max(domain_scores.values()) if domain_scores else 0
        return max_score

    async def _execute_hybrid_reasoning(self,
                                       reasoning_mode: ReasoningMode,
                                       patent_data: Dict[str, Any],
                                       context: Dict[str, Any],
                                       rule_result: ReasoningResult,
                                       neural_result: Dict[str, Any]) -> HybridReasoningResult:
        """执行混合推理"""

        if reasoning_mode == ReasoningMode.RULE_ONLY:
            return self._create_rule_only_result(rule_result)

        elif reasoning_mode == ReasoningMode.NEURAL_ONLY:
            return self._create_neural_only_result(neural_result)

        elif reasoning_mode == ReasoningMode.HYBRID_SEQUENTIAL:
            return await self._sequential_hybrid_reasoning(rule_result, neural_result)

        elif reasoning_mode == ReasoningMode.HYBRID_PARALLEL:
            return await self._parallel_hybrid_reasoning(rule_result, neural_result, patent_data)

        else:  # ADAPTIVE
            return await self._adaptive_hybrid_reasoning(rule_result, neural_result, patent_data)

    def _create_rule_only_result(self, rule_result: ReasoningResult) -> HybridReasoningResult:
        """创建纯规则推理结果"""
        return HybridReasoningResult(
            conclusion=rule_result.conclusion,
            confidence=rule_result.confidence,
            rule_contribution=1.0,
            neural_contribution=0.0,
            fusion_score=rule_result.confidence,
            reasoning_path=rule_result.reasoning_path,
            ensemble_decisions={'rule': rule_result.confidence},
            meta_features={'mode': 'rule_only'}
        )

    def _create_neural_only_result(self, neural_result: Dict[str, Any]) -> HybridReasoningResult:
        """创建纯神经网络推理结果"""
        # 基于神经网络输出生成结论
        avg_score = (
            neural_result['novelty_score'] +
            neural_result['inventive_score'] +
            neural_result['practical_score']
        ) / 3

        conclusion = f"神经网络分析: 新颖性({neural_result['novelty_score']:.2f}) " \
                   f"创造性({neural_result['inventive_score']:.2f}) " \
                   f"实用性({neural_result['practical_score']:.2f})"

        return HybridReasoningResult(
            conclusion=conclusion,
            confidence=neural_result['confidence_score'],
            rule_contribution=0.0,
            neural_contribution=1.0,
            fusion_score=neural_result['confidence_score'],
            reasoning_path=['神经网络特征提取', '深度学习推理', '结果生成'],
            ensemble_decisions={'neural': neural_result['confidence_score']},
            meta_features={'mode': 'neural_only'}
        )

    async def _sequential_hybrid_reasoning(self,
                                          rule_result: ReasoningResult,
                                          neural_result: Dict[str, Any]) -> HybridReasoningResult:
        """顺序混合推理"""
        # 先规则推理，再神经网络补充
        base_confidence = rule_result.confidence
        neural_boost = neural_result['confidence_score'] * 0.3

        final_confidence = min(base_confidence + neural_boost, 1.0)
        rule_contribution = 0.7
        neural_contribution = 0.3

        conclusion = f"顺序混合推理: {rule_result.conclusion}，" \
                   f"神经网络补充确认，综合置信度: {final_confidence:.2f}"

        return HybridReasoningResult(
            conclusion=conclusion,
            confidence=final_confidence,
            rule_contribution=rule_contribution,
            neural_contribution=neural_contribution,
            fusion_score=final_confidence,
            reasoning_path=rule_result.reasoning_path + ['神经网络验证'],
            ensemble_decisions={
                'rule': rule_result.confidence,
                'neural': neural_result['confidence_score']
            },
            meta_features={'mode': 'sequential'}
        )

    async def _parallel_hybrid_reasoning(self,
                                        rule_result: ReasoningResult,
                                        neural_result: Dict[str, Any],
                                        patent_data: Dict[str, Any]) -> HybridReasoningResult:
        """并行混合推理"""

        # 使用注意力融合
        rule_conf = rule_result.confidence
        neural_conf = neural_result['confidence_score']

        # 动态权重计算
        total_conf = rule_conf + neural_conf
        if total_conf == 0:
            rule_weight = neural_weight = 0.5
        else:
            rule_weight = rule_conf / total_conf
            neural_weight = neural_conf / total_conf

        # 加权融合
        fused_confidence = rule_conf * rule_weight + neural_conf * neural_weight

        conclusion = f"并行混合推理: 规则推理({rule_conf:.2f}) + " \
                   f"神经网络({neural_conf:.2f}) = 综合决策({fused_confidence:.2f})"

        return HybridReasoningResult(
            conclusion=conclusion,
            confidence=fused_confidence,
            rule_contribution=rule_weight,
            neural_contribution=neural_weight,
            fusion_score=fused_confidence,
            reasoning_path=['规则推理并行执行', '神经网络并行执行', '注意力融合'],
            ensemble_decisions={
                'rule': rule_conf,
                'neural': neural_conf
            },
            meta_features={'mode': 'parallel'}
        )

    async def _adaptive_hybrid_reasoning(self,
                                        rule_result: ReasoningResult,
                                        neural_result: Dict[str, Any],
                                        patent_data: Dict[str, Any]) -> HybridReasoningResult:
        """自适应混合推理"""

        # 基于数据特征自适应调整
        complexity = self._assess_data_complexity(patent_data)
        domain_specific = self._assess_domain_specificity(patent_data)

        # 复杂度高时更依赖神经网络
        if complexity > 0.7:
            neural_bias = 0.2 + (complexity - 0.7) * 0.6
        else:
            neural_bias = 0.2

        # 领域特异性高时更依赖规则
        if domain_specific > 0.6:
            rule_bias = 0.2 + (domain_specific - 0.6) * 0.5
        else:
            rule_bias = 0.2

        # 归一化权重
        total_bias = neural_bias + rule_bias
        neural_weight = neural_bias / total_bias
        rule_weight = rule_bias / total_bias

        # 计算融合结果
        rule_conf = rule_result.confidence
        neural_conf = neural_result['confidence_score']

        fused_confidence = rule_conf * rule_weight + neural_conf * neural_weight

        conclusion = f"自适应混合推理: 复杂度({complexity:.2f}) " \
                   f"领域特异性({domain_specific:.2f}) " \
                   f"-> 规则权重({rule_weight:.2f}) 神经权重({neural_weight:.2f}) " \
                   f"综合置信度({fused_confidence:.2f})"

        return HybridReasoningResult(
            conclusion=conclusion,
            confidence=fused_confidence,
            rule_contribution=rule_weight,
            neural_contribution=neural_weight,
            fusion_score=fused_confidence,
            reasoning_path=[
                '数据特征分析',
                '自适应权重计算',
                '规则推理',
                '神经网络推理',
                '动态融合'
            ],
            ensemble_decisions={
                'rule': rule_conf,
                'neural': neural_conf
            },
            meta_features={
                'mode': 'adaptive',
                'complexity': complexity,
                'domain_specific': domain_specific
            }
        )

    async def _evaluate_and_learn(self,
                                patent_data: Dict[str, Any],
                                rule_result: ReasoningResult,
                                neural_result: Dict[str, Any],
                                hybrid_result: HybridReasoningResult):
        """评估推理结果并学习"""

        # 记录学习历史
        learning_record = {
            'timestamp': datetime.now(),
            'patent_id': patent_data.get('patent_id'),
            'rule_confidence': rule_result.confidence,
            'neural_confidence': neural_result['confidence_score'],
            'hybrid_confidence': hybrid_result.confidence,
            'rule_contribution': hybrid_result.rule_contribution,
            'neural_contribution': hybrid_result.neural_contribution,
            'fusion_improvement': hybrid_result.confidence - max(rule_result.confidence, neural_result['confidence_score'])
        }

        self.learning_history.append(learning_record)

        # 限制历史记录长度
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-1000:]

    def _update_performance_metrics(self, reasoning_mode: ReasoningMode, result: HybridReasoningResult):
        """更新性能指标"""
        self.performance_metrics['total_reasonings'] += 1
        self.performance_metrics['mode_usage'][reasoning_mode.value] += 1

        # 更新平均置信度
        current_avg = self.performance_metrics['average_confidence']
        total = self.performance_metrics['total_reasonings']
        self.performance_metrics['average_confidence'] = (
            (current_avg * (total - 1) + result.confidence) / total
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total = self.performance_metrics['total_reasonings']
        if total == 0:
            return {}

        # 计算模式使用百分比
        mode_usage_pct = {}
        for mode, count in self.performance_metrics['mode_usage'].items():
            mode_usage_pct[mode] = (count / total) * 100

        return {
            'total_reasonings': total,
            'average_confidence': self.performance_metrics['average_confidence'],
            'mode_usage': self.performance_metrics['mode_usage'],
            'mode_usage_pct': mode_usage_pct,
            'learning_records': len(self.learning_history)
        }

    def export_models(self, export_dir: str):
        """导出模型和配置"""
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        # 导出神经网络模型
        torch.save(self.neural_network.state_dict(), export_path / 'patent_neural_network.pth')
        torch.save(self.attention_fusion.state_dict(), export_path / 'attention_fusion.pth')
        torch.save(self.meta_learner.state_dict(), export_path / 'meta_learner.pth')

        # 导出配置和性能指标
        with open(export_path / 'hybrid_reasoning_config.json', 'w', encoding='utf-8') as f:
            json.dump({
                'reasoning_mode': self.reasoning_mode.value,
                'fusion_strategy': self.fusion_strategy.value,
                'performance_metrics': self.performance_metrics
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 混合推理模型已导出到: {export_dir}")

async def main():
    """主函数"""
    logger.info('🧠 混合推理架构测试')
    logger.info('Athena + 小诺 为您服务~ 💖')
    logger.info(str('='*50))

    # 初始化混合推理引擎
    engine = HybridReasoningEngine()

    # 测试用例
    test_patents = [
        {
            'patent_id': 'CN202512050003',
            'title': '基于深度学习的智能专利审查系统',
            'abstract': '本发明提供一种结合多种人工智能技术的专利审查系统',
            'technical_field': '人工智能',
            'patent_type': 'invention',
            'novelty_score': 0.75,
            'inventive_score': 0.68,
            'practical_score': 0.85,
            'keywords': ['深度学习', '专利审查', '人工智能', '智能系统'],
            'claims': '1. 一种基于深度学习的智能专利审查系统...',
            'description': '本发明涉及人工智能技术领域...'
        },
        {
            'patent_id': 'CN202512050004',
            'title': '新型机械传动装置',
            'abstract': '本发明涉及一种改进的机械传动结构',
            'technical_field': '机械工程',
            'patent_type': 'invention',
            'novelty_score': 0.45,
            'inventive_score': 0.38,
            'practical_score': 0.90,
            'keywords': ['机械', '传动', '装置', '结构'],
            'claims': '1. 一种新型机械传动装置...',
            'description': '本发明属于机械技术领域...'
        },
        {
            'patent_id': 'CN202512050005',
            'title': '复杂化学合成方法',
            'abstract': '本发明提供一种多步骤的化学物质合成方法',
            'technical_field': '化学工程',
            'patent_type': 'invention',
            'novelty_score': 0.65,
            'inventive_score': 0.72,
            'practical_score': 0.78,
            'keywords': ['化学', '合成', '方法', '化合物'],
            'claims': '1. 一种复杂化学合成方法...',
            'description': '本发明涉及化学合成技术...'
        }
    ]

    # 测试上下文
    test_context = {
        'urgency_level': 0.7,
        'complexity_score': 0.8,
        'related_patents': ['CN202012345', 'CN202112345', 'CN202212345'],
        'expedited_review': True
    }

    # 执行混合推理测试
    for i, patent in enumerate(test_patents, 1):
        logger.info(f"\n📋 测试专利 {i}: {patent['title']}")
        logger.info(str('-' * 60))

        try:
            result = await engine.hybrid_reason(patent, test_context)

            logger.info(f"推理结论: {result.conclusion}")
            logger.info(f"置信度: {result.confidence:.2f}")
            logger.info(f"规则贡献: {result.rule_contribution:.2f}")
            logger.info(f"神经网络贡献: {result.neural_contribution:.2f}")
            logger.info(f"融合分数: {result.fusion_score:.2f}")
            logger.info(f"处理时间: {result.processing_time:.2f}秒")

            logger.info(f"\n🔍 推理路径:")
            for step in result.reasoning_path:
                logger.info(f"  → {step}")

            logger.info(f"\n📊 集成决策:")
            for method, score in result.ensemble_decisions.items():
                logger.info(f"  {method}: {score:.2f}")

        except Exception as e:
            logger.info(f"❌ 处理失败: {e}")

    # 性能报告
    performance = engine.get_performance_report()
    if performance:
        logger.info(f"\n📈 混合推理性能报告:")
        logger.info(f"总推理次数: {performance['total_reasonings']}")
        logger.info(f"平均置信度: {performance['average_confidence']:.2f}")
        logger.info(f"学习记录数: {performance['learning_records']}")

        logger.info(f"\n🎯 推理模式使用分布:")
        for mode, pct in performance['mode_usage_pct'].items():
            if pct > 0:
                logger.info(f"  {mode}: {pct:.1f}%")

    # 导出模型
    engine.export_models('hybrid_reasoning_models')
    logger.info(f"\n✅ 混合推理架构测试完成！模型已导出")

if __name__ == '__main__':
    asyncio.run(main())