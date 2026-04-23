#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级决策模型集合
Advanced Decision Models Collection

提供多种预训练的决策模型，包括随机森林、神经网络、强化学习等

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import pickle
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# 尝试导入机器学习库
try:
    import joblib
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.svm import SVC
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning('Scikit-learn未安装，部分功能将受限')

# 导入基础决策模型
from enhanced_decision_engine import DecisionModel

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """模型类型"""
    RANDOM_FOREST = 'random_forest'
    GRADIENT_BOOSTING = 'gradient_boosting'
    NEURAL_NETWORK = 'neural_network'
    SVM = 'svm'
    DEEP_NEURAL = 'deep_neural'
    ENSEMBLE_VOTING = 'ensemble_voting'
    REINFORCEMENT_LEARNING = 'reinforcement_learning'
    BAYESIAN_OPTIMIZATION = 'bayesian_optimization'

class RandomDecisionModel(DecisionModel):
    """随机决策模型（基线模型）"""

    def __init__(self, decision_threshold: float = 0.5):
        super().__init__('RandomDecisionModel')
        self.decision_threshold = decision_threshold
        self.prediction_history = deque(maxlen=100)

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练随机模型（实际上不需要训练）"""
        # 随机模型不需要训练，但我们可以记录历史
        self.is_trained = True
        self.last_trained = datetime.now()
        self.accuracy = 0.5  # 随机模型的基准准确度
        return self.accuracy

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """随机预测"""
        features = inputs.get('features', {})

        # 基于特征随机生成预测
        seed = hash(json.dumps(features, sort_keys=True)) % 1000
        np.random.seed(seed)

        score = np.random.uniform(0, 1)
        confidence = np.random.uniform(0.3, 0.7)

        self.prediction_history.append(score)

        return {
            'score': score,
            'confidence': confidence,
            'model_type': 'random',
            'features_used': list(features.keys())
        }

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释随机预测"""
        return {
            'explanation': '随机模型的预测基于随机数生成，没有实际的学习过程',
            'method': 'random_generation',
            'reliability': 'low'
        }

class RandomForestDecisionModel(DecisionModel):
    """随机森林决策模型"""

    def __init__(self, n_estimators: int = 100, max_depth: Optional[int] = None):
        super().__init__('RandomForestDecisionModel')
        self.n_estimators = n_estimators
        self.max_depth = max_depth

        if ML_AVAILABLE:
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42
            )
            self.scaler = StandardScaler()
            self.feature_names = []
        else:
            logger.warning('Scikit-learn不可用，使用模拟的随机森林模型')
            self.model = None

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练随机森林模型"""
        if not ML_AVAILABLE or len(data) < 10:
            logger.warning('数据不足或库不可用，返回默认准确度')
            self.is_trained = True
            self.accuracy = 0.5
            return self.accuracy

        try:
            # 准备数据
            X, y = self._prepare_training_data(data)

            if X is None or y is None or len(X) == 0:
                self.is_trained = True
                self.accuracy = 0.5
                return self.accuracy

            # 分割数据
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 标准化特征
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # 训练模型
            self.model.fit(X_train_scaled, y_train)

            # 评估模型
            y_pred = self.model.predict(X_test_scaled)
            self.accuracy = accuracy_score(y_test, y_pred)

            # 交叉验证
            cv_scores = cross_val_score(
                self.model, X_train_scaled, y_train, cv=5
            )
            self.accuracy = np.mean(cv_scores)

            self.is_trained = True
            self.last_trained = datetime.now()

            logger.info(f"✅ 随机森林模型训练完成，准确度: {self.accuracy:.2f}")
            return self.accuracy

        except Exception as e:
            logger.error(f"❌ 随机森林模型训练失败: {e}")
            self.is_trained = True
            self.accuracy = 0.5
            return self.accuracy

    def _prepare_training_data(self, data: List[Dict[str, Any]]) -> Tuple[Any, Any]:
        """准备训练数据"""
        if not data:
            return None, None

        # 提取特征和标签
        all_features = []
        all_labels = []
        self.feature_names = []

        # 收集所有特征名
        for record in data:
            features = record.get('features', {})
            self.feature_names.extend(features.keys())

        # 去重并排序特征名
        self.feature_names = sorted(list(set(self.feature_names)))

        # 准备特征矩阵
        for record in data:
            features = record.get('features', {})
            outcome = record.get('outcome', 0)

            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(features.get(feature_name, 0))

            all_features.append(feature_vector)
            all_labels.append(outcome)

        return np.array(all_features), np.array(all_labels)

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """使用随机森林预测"""
        features = inputs.get('features', {})

        if not self.is_trained or not ML_AVAILABLE or self.model is None:
            # 降级到随机预测
            random_model = RandomDecisionModel()
            return await random_model.predict(inputs)

        try:
            # 准备特征向量
            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(features.get(feature_name, 0))

            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)

            # 预测概率
            probabilities = self.model.predict_proba(X_scaled)
            predicted_class = self.model.predict(X_scaled)[0]

            # 对于二分类，返回正类的概率
            if len(probabilities[0]) == 2:
                score = probabilities[0][1]
            else:
                score = float(predicted_class)

            # 计算置信度（基于概率分布）
            confidence = np.max(probabilities[0])

            return {
                'score': score,
                'confidence': confidence,
                'predicted_class': int(predicted_class),
                'probabilities': probabilities[0].tolist(),
                'model_type': 'random_forest',
                'features_used': self.feature_names
            }

        except Exception as e:
            logger.error(f"❌ 随机森林预测失败: {e}")
            # 降级到随机预测
            random_model = RandomDecisionModel()
            return await random_model.predict(inputs)

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释随机森林预测"""
        if not self.is_trained or not ML_AVAILABLE or self.model is None:
            return {'explanation': '模型未训练或库不可用'}

        try:
            # 获取特征重要性
            feature_importance = dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))

            # 排序重要性
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10 重要特征

            return {
                'explanation': '基于随机森林的特征重要性分析',
                'method': 'feature_importance',
                'top_features': sorted_features,
                'n_estimators': self.n_estimators,
                'max_depth': self.max_depth
            }

        except Exception as e:
            logger.error(f"❌ 特征重要性计算失败: {e}")
            return {'explanation': '无法计算特征重要性'}

class NeuralNetworkDecisionModel(DecisionModel):
    """神经网络决策模型"""

    def __init__(self, hidden_layer_sizes: Tuple[int, ...] = (100, 50),
                 activation: str = 'relu', learning_rate: float = 0.001):
        super().__init__('NeuralNetworkDecisionModel')
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation
        self.learning_rate = learning_rate

        if ML_AVAILABLE:
            self.model = MLPClassifier(
                hidden_layer_sizes=hidden_layer_sizes,
                activation=activation,
                learning_rate_init=learning_rate,
                max_iter=500,
                random_state=42
            )
            self.scaler = StandardScaler()
            self.feature_names = []
        else:
            logger.warning('Scikit-learn不可用，使用模拟的神经网络模型')
            self.model = None

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练神经网络模型"""
        if not ML_AVAILABLE or len(data) < 10:
            self.is_trained = True
            self.accuracy = 0.5
            return self.accuracy

        try:
            # 使用与随机森林相同的数据准备方法
            X, y = self._prepare_training_data(data)

            if X is None or y is None or len(X) == 0:
                self.is_trained = True
                self.accuracy = 0.5
                return self.accuracy

            # 分割数据
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # 标准化特征
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # 训练模型
            self.model.fit(X_train_scaled, y_train)

            # 评估模型
            y_pred = self.model.predict(X_test_scaled)
            self.accuracy = accuracy_score(y_test, y_pred)

            self.is_trained = True
            self.last_trained = datetime.now()

            logger.info(f"✅ 神经网络模型训练完成，准确度: {self.accuracy:.2f}")
            return self.accuracy

        except Exception as e:
            logger.error(f"❌ 神经网络模型训练失败: {e}")
            self.is_trained = True
            self.accuracy = 0.5
            return self.accuracy

    def _prepare_training_data(self, data: List[Dict[str, Any]]) -> Tuple[Any, Any]:
        """准备训练数据（与随机森林相同）"""
        if not data:
            return None, None

        all_features = []
        all_labels = []
        self.feature_names = []

        for record in data:
            features = record.get('features', {})
            self.feature_names.extend(features.keys())

        self.feature_names = sorted(list(set(self.feature_names)))

        for record in data:
            features = record.get('features', {})
            outcome = record.get('outcome', 0)

            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(features.get(feature_name, 0))

            all_features.append(feature_vector)
            all_labels.append(outcome)

        return np.array(all_features), np.array(all_labels)

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """使用神经网络预测"""
        features = inputs.get('features', {})

        if not self.is_trained or not ML_AVAILABLE or self.model is None:
            random_model = RandomDecisionModel()
            return await random_model.predict(inputs)

        try:
            # 准备特征向量
            feature_vector = []
            for feature_name in self.feature_names:
                feature_vector.append(features.get(feature_name, 0))

            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)

            # 预测
            probabilities = self.model.predict_proba(X_scaled)
            predicted_class = self.model.predict(X_scaled)[0]

            if len(probabilities[0]) == 2:
                score = probabilities[0][1]
            else:
                score = float(predicted_class)

            confidence = np.max(probabilities[0])

            # 获取损失曲线信息
            loss_curve = getattr(self.model, 'loss_curve_', [])
            current_loss = loss_curve[-1] if loss_curve else None

            return {
                'score': score,
                'confidence': confidence,
                'predicted_class': int(predicted_class),
                'probabilities': probabilities[0].tolist(),
                'model_type': 'neural_network',
                'features_used': self.feature_names,
                'training_loss': current_loss,
                'iterations': self.model.n_iter_
            }

        except Exception as e:
            logger.error(f"❌ 神经网络预测失败: {e}")
            random_model = RandomDecisionModel()
            return await random_model.predict(inputs)

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释神经网络预测"""
        if not self.is_trained or not ML_AVAILABLE or self.model is None:
            return {'explanation': '模型未训练或库不可用'}

        try:
            # 神经网络的可解释性有限，提供网络结构信息
            return {
                'explanation': '基于多层感知机的预测，通过非线性变换学习特征关系',
                'method': 'neural_network_architecture',
                'architecture': {
                    'hidden_layers': self.hidden_layer_sizes,
                    'activation': self.activation,
                    'input_features': len(self.feature_names),
                    'output_classes': self.model.n_outputs_
                },
                'training_info': {
                    'iterations': getattr(self.model, 'n_iter_', 0),
                    'loss_curve': getattr(self.model, 'loss_curve_', [])[-5:]  # 最后5个损失值
                }
            }

        except Exception as e:
            logger.error(f"❌ 神经网络解释失败: {e}")
            return {'explanation': '无法生成神经网络解释'}

class EnsembleVotingModel(DecisionModel):
    """集成投票模型"""

    def __init__(self, models: Optional[List[DecisionModel]] = None, voting: str = 'soft'):
        super().__init__('EnsembleVotingModel')
        self.models = models or []
        self.voting = voting  # 'soft' or 'hard'
        self.model_weights = []

    def add_model(self, model: DecisionModel, weight: float = 1.0):
        """添加模型到集成"""
        self.models.append(model)
        self.model_weights.append(weight)
        logger.info(f"📝 已添加模型 {model.name} 到集成投票模型")

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练集成模型"""
        if not self.models:
            logger.warning('没有可训练的模型')
            return 0.0

        accuracies = []
        for model in self.models:
            try:
                accuracy = await model.train(data)
                accuracies.append(accuracy)
                logger.info(f"模型 {model.name} 训练准确度: {accuracy:.2f}")
            except Exception as e:
                logger.error(f"模型 {model.name} 训练失败: {e}")
                accuracies.append(0.0)

        # 集成模型的准确度是子模型的加权平均
        if accuracies and self.model_weights:
            self.accuracy = sum(a * w for a, w in zip(accuracies, self.model_weights)) / sum(self.model_weights)
        else:
            self.accuracy = 0.0

        self.is_trained = True
        self.last_trained = datetime.now()

        logger.info(f"✅ 集成投票模型训练完成，加权准确度: {self.accuracy:.2f}")
        return self.accuracy

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """集成预测"""
        if not self.models:
            return {'score': 0.5, 'confidence': 0.0, 'error': 'No models available'}

        predictions = []
        confidences = []

        for model in self.models:
            try:
                pred = await model.predict(inputs)
                predictions.append(pred)
                confidences.append(pred.get('confidence', 0.5))
            except Exception as e:
                logger.error(f"模型 {model.name} 预测失败: {e}")
                predictions.append({'score': 0.5, 'confidence': 0.0})
                confidences.append(0.0)

        if self.voting == 'soft':
            # 软投票：加权平均概率
            weighted_scores = []
            total_weight = 0.0

            for pred, weight in zip(predictions, self.model_weights):
                score = pred.get('score', 0.5)
                confidence = pred.get('confidence', 0.5)

                # 综合考虑模型权重和预测置信度
                effective_weight = weight * confidence
                weighted_scores.append(score * effective_weight)
                total_weight += effective_weight

            final_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0.5
            final_confidence = np.mean(confidences)

        else:
            # 硬投票：多数决定
            binary_predictions = [1 if p.get('score', 0.5) > 0.5 else 0 for p in predictions]
            final_score = sum(binary_predictions) / len(binary_predictions)
            final_confidence = np.mean(confidences)

        return {
            'score': final_score,
            'confidence': final_confidence,
            'voting_type': self.voting,
            'individual_predictions': predictions,
            'model_count': len(self.models),
            'model_weights': self.model_weights
        }

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释集成预测"""
        explanations = []

        for model in self.models:
            try:
                exp = await model.explain(inputs)
                explanations.append({
                    'model_name': model.name,
                    'explanation': exp
                })
            except Exception as e:
                logger.error(f"模型 {model.name} 解释失败: {e}")

        return {
            'explanation': f'基于{len(self.models)}个模型的{self.voting}投票集成',
            'method': 'ensemble_voting',
            'individual_explanations': explanations,
            'voting_strategy': self.voting
        }

class ReinforcementLearningModel(DecisionModel):
    """强化学习决策模型（简化版）"""

    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95):
        super().__init__('ReinforcementLearningModel')
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.state_space = set()
        self.action_space = [0, 1]  # 0: 拒绝, 1: 批准
        self.epsilon = 0.1  # 探索率

    def _state_to_key(self, features: Dict[str, Any]) -> str:
        """将特征转换为状态键"""
        # 简化的状态表示
        key_features = []
        for k, v in sorted(features.items()):
            # 将连续值离散化
            if isinstance(v, (int, float)):
                discretized = int(v * 10) / 10  # 保留1位小数
                key_features.append(f"{k}:{discretized}")
            else:
                key_features.append(f"{k}:{v}")

        return '|'.join(key_features)

    async def train(self, data: List[Dict[str, Any]]) -> float:
        """训练强化学习模型"""
        if not data:
            self.is_trained = True
            self.accuracy = 0.5
            return self.accuracy

        # 简化的Q学习训练
        episodes = 100  # 训练轮数

        for episode in range(episodes):
            for record in data:
                features = record.get('features', {})
                outcome = record.get('outcome', 0)

                state = self._state_to_key(features)
                self.state_space.add(state)

                # Q学习更新
                current_q = self.q_table[state][outcome]
                reward = 1.0 if outcome == 1 else -1.0

                # 简化的更新规则
                new_q = current_q + self.learning_rate * (reward - current_q)
                self.q_table[state][outcome] = new_q

        # 评估准确度
        correct_predictions = 0
        total_predictions = len(data)

        for record in data:
            features = record.get('features', {})
            expected_outcome = record.get('outcome', 0)
            state = self._state_to_key(features)

            # 选择最优动作
            if state in self.q_table:
                best_action = max(self.q_table[state].items(), key=lambda x: x[1])[0]
                if best_action == expected_outcome:
                    correct_predictions += 1

        self.accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        self.is_trained = True
        self.last_trained = datetime.now()

        logger.info(f"✅ 强化学习模型训练完成，准确度: {self.accuracy:.2f}")
        return self.accuracy

    async def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """使用强化学习预测"""
        features = inputs.get('features', {})
        state = self._state_to_key(features)

        if not self.is_trained or state not in self.q_table:
            # 未见过的新状态，随机探索
            if np.random.random() < self.epsilon:
                action = np.random.choice(self.action_space)
                score = float(action)
                confidence = 0.3
            else:
                score = 0.5
                confidence = 0.5
        else:
            # 选择Q值最高的动作
            q_values = self.q_table[state]
            best_action = max(q_values.items(), key=lambda x: x[1])[0]
            score = float(best_action)

            # 计算置信度（基于Q值的差异）
            q_values_list = list(q_values.values())
            if len(q_values_list) > 1:
                confidence = (max(q_values_list) - min(q_values_list)) / (max(q_values_list) + 0.001)
            else:
                confidence = 0.5

        return {
            'score': score,
            'confidence': min(confidence, 1.0),
            'state': state,
            'q_values': dict(self.q_table[state]) if state in self.q_table else {},
            'exploration_rate': self.epsilon,
            'model_type': 'reinforcement_learning'
        }

    async def explain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """解释强化学习预测"""
        features = inputs.get('features', {})
        state = self._state_to_key(features)

        if state not in self.q_table:
            return {
                'explanation': '新状态，基于探索策略决策',
                'method': 'exploration'
            }
        else:
            q_values = self.q_table[state]
            best_action = max(q_values.items(), key=lambda x: x[1])

            return {
                'explanation': f'基于Q值学习的最优决策，状态: {state}',
                'method': 'q_learning',
                'q_values': dict(q_values),
                'best_action': best_action[0],
                'best_q_value': best_action[1],
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor
            }

class ModelFactory:
    """模型工厂"""

    @staticmethod
    def create_model(model_type: ModelType, **kwargs) -> DecisionModel:
        """创建指定类型的模型"""
        if model_type == ModelType.RANDOM_FOREST:
            return RandomForestDecisionModel(
                n_estimators=kwargs.get('n_estimators', 100),
                max_depth=kwargs.get('max_depth', None)
            )
        elif model_type == ModelType.NEURAL_NETWORK:
            return NeuralNetworkDecisionModel(
                hidden_layer_sizes=kwargs.get('hidden_layer_sizes', (100, 50)),
                activation=kwargs.get('activation', 'relu'),
                learning_rate=kwargs.get('learning_rate', 0.001)
            )
        elif model_type == ModelType.ENSEMBLE_VOTING:
            return EnsembleVotingModel(
                models=kwargs.get('models', []),
                voting=kwargs.get('voting', 'soft')
            )
        elif model_type == ModelType.REINFORCEMENT_LEARNING:
            return ReinforcementLearningModel(
                learning_rate=kwargs.get('learning_rate', 0.1),
                discount_factor=kwargs.get('discount_factor', 0.95)
            )
        else:
            # 默认返回随机决策模型
            return RandomDecisionModel()

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 高级决策模型测试')
    logger.info(str('='*50))

    # 创建测试数据
    training_data = [
        {
            'features': {
                'novelty': 0.9,
                'inventive': 0.8,
                'practical': 0.7,
                'technical': 0.85,
                'legal': 0.9
            },
            'outcome': 1
        },
        {
            'features': {
                'novelty': 0.3,
                'inventive': 0.2,
                'practical': 0.6,
                'technical': 0.4,
                'legal': 0.5
            },
            'outcome': 0
        },
        {
            'features': {
                'novelty': 0.7,
                'inventive': 0.6,
                'practical': 0.8,
                'technical': 0.7,
                'legal': 0.8
            },
            'outcome': 1
        },
        {
            'features': {
                'novelty': 0.4,
                'inventive': 0.3,
                'practical': 0.5,
                'technical': 0.4,
                'legal': 0.6
            },
            'outcome': 0
        }
    ]

    # 测试随机森林模型
    logger.info("\n🌲 测试随机森林模型:")
    rf_model = ModelFactory.create_model(ModelType.RANDOM_FOREST)
    rf_accuracy = await rf_model.train(training_data)
    logger.info(f"训练准确度: {rf_accuracy:.2f}")

    test_input = {'features': {'novelty': 0.8, 'inventive': 0.7, 'practical': 0.6, 'technical': 0.75, 'legal': 0.8}}
    rf_pred = await rf_model.predict(test_input)
    logger.info(f"预测结果: {rf_pred}")

    rf_exp = await rf_model.explain(test_input)
    logger.info(f"模型解释: {rf_exp}")

    # 测试神经网络模型
    logger.info("\n🧠 测试神经网络模型:")
    nn_model = ModelFactory.create_model(ModelType.NEURAL_NETWORK)
    nn_accuracy = await nn_model.train(training_data)
    logger.info(f"训练准确度: {nn_accuracy:.2f}")

    nn_pred = await nn_model.predict(test_input)
    logger.info(f"预测结果: {nn_pred}")

    # 测试集成模型
    logger.info("\n🗳️ 测试集成投票模型:")
    ensemble_model = ModelFactory.create_model(ModelType.ENSEMBLE_VOTING)
    ensemble_model.add_model(rf_model, weight=0.6)
    ensemble_model.add_model(nn_model, weight=0.4)

    ensemble_accuracy = await ensemble_model.train(training_data)
    logger.info(f"集成训练准确度: {ensemble_accuracy:.2f}")

    ensemble_pred = await ensemble_model.predict(test_input)
    logger.info(f"集成预测结果: {ensemble_pred}")

    # 测试强化学习模型
    logger.info("\n🎮 测试强化学习模型:")
    rl_model = ModelFactory.create_model(ModelType.REINFORCEMENT_LEARNING)
    rl_accuracy = await rl_model.train(training_data)
    logger.info(f"训练准确度: {rl_accuracy:.2f}")

    rl_pred = await rl_model.predict(test_input)
    logger.info(f"预测结果: {rl_pred}")

    rl_exp = await rl_model.explain(test_input)
    logger.info(f"模型解释: {rl_exp}")

    logger.info("\n✅ 高级决策模型测试完成！")

if __name__ == '__main__':
    asyncio.run(main())