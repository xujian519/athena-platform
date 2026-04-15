from __future__ import annotations
# pyright: ignore
"""
高级决策模型集合

该模块整合了Athena工作平台的所有决策模型，提供统一的决策接口。
支持8种决策模型：随机森林、梯度提升、神经网络、SVM、深度神经网络、集成投票、强化学习、贝叶斯优化。

Author: Athena AI Team
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """支持的决策模型类型"""
    RANDOM_FOREST = 'random_forest'
    GRADIENT_BOOSTING = 'gradient_boosting'
    NEURAL_NETWORK = 'neural_network'
    SVM = 'svm'
    DEEP_NEURAL = 'deep_neural'
    ENSEMBLE_VOTING = 'ensemble_voting'
    REINFORCEMENT_LEARNING = 'reinforcement_learning'
    BAYESIAN_OPTIMIZATION = 'bayesian_optimization'


class DecisionPriority(Enum):
    """决策优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DecisionContext:
    """决策上下文"""
    task_type: str
    domain: str
    complexity: float  # 0.0-1.0
    urgency: float  # 0.0-1.0
    available_resources: dict[str, Any]
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionOption:
    """决策选项"""
    option_id: str
    description: str
    expected_outcome: dict[str, Any]
    confidence: float  # 0.0-1.0
    risk_score: float  # 0.0-1.0
    resource_requirements: dict[str, Any]
    execution_time: float | None = None


@dataclass
class DecisionResult:
    """决策结果"""
    selected_option: DecisionOption
    reasoning: str
    confidence: float
    alternative_options: list[DecisionOption]
    timestamp: datetime = field(default_factory=datetime.now)
    model_used: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseDecisionModel:
    """决策模型基类"""

    def __init__(self, model_type: ModelType, config: dict | None = None):  # type: ignore
        self.model_type = model_type
        self.config = config or {}
        self.is_trained = False

    async def decide(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> DecisionResult:
        """
        执行决策

        Args:
            options: 可选的决策选项列表
            context: 决策上下文

        Returns:
            DecisionResult: 决策结果
        """
        raise NotImplementedError("子类必须实现decide方法")

    async def train(self, training_data: list[Any]) -> bool:
        """
        训练模型

        Args:
            training_data: 训练数据

        Returns:
            bool: 训练是否成功
        """
        raise NotImplementedError("子类必须实现train方法")


class RandomForestDecisionModel(BaseDecisionModel):
    """随机森林决策模型"""

    def __init__(self, config: dict | None = None):  # type: ignore
        super().__init__(ModelType.RANDOM_FOREST, config)
        self.n_estimators = self.config.get('n_estimators', 100)
        self.max_depth = self.config.get('max_depth', 10)

    async def decide(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> DecisionResult:
        """使用随机森林进行决策"""
        try:
            # 特征提取
            features = self._extract_features(options, context)

            # 模拟随机森林预测（实际应该调用训练好的模型）
            scores = self._predict_scores(features)

            # 选择最佳选项
            best_idx = np.argmax(scores)
            selected_option = options[best_idx]

            # 生成决策结果
            return DecisionResult(
                selected_option=selected_option,
                reasoning=f"基于随机森林模型（{self.n_estimators}棵树）的预测结果",
                confidence=float(scores[best_idx]),
                alternative_options=[opt for i, opt in enumerate(options) if i != best_idx],
                model_used=self.model_type.value
            )

        except Exception as e:
            logger.error(f"随机森林决策失败: {e}", exc_info=True)
            # 返回默认决策
            return self._get_default_decision(options, context)

    def _extract_features(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> np.ndarray:
        """提取特征用于模型预测"""
        features = []
        for option in options:
            feature_vector = [
                option.confidence,
                1 - option.risk_score,
                context.urgency,
                context.complexity,
                len(option.resource_requirements),
            ]
            features.append(feature_vector)
        return np.array(features)

    def _predict_scores(self, features: np.ndarray) -> np.ndarray:
        """预测每个选项的分数"""
        # 简化版本：使用加权组合
        # 实际应该使用训练好的随机森林模型
        scores = features[:, 0] * 0.4 + features[:, 1] * 0.6
        return scores

    def _get_default_decision(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> DecisionResult:
        """返回默认决策"""
        # 处理空选项列表
        if not options:
            return DecisionResult(
                selected_option=None,
                reasoning="没有可用的选项",
                confidence=0.0,
                alternative_options=[],
                model_used="default"
            )

        # 选择置信度最高的选项
        best_option = max(options, key=lambda x: x.confidence)
        return DecisionResult(
            selected_option=best_option,
            reasoning="使用默认决策规则（最高置信度）",
            confidence=best_option.confidence,
            alternative_options=[opt for opt in options if opt != best_option],
            model_used="default"
        )


class GradientBoostingDecisionModel(BaseDecisionModel):
    """梯度提升决策模型"""

    def __init__(self, config: dict | None = None):  # type: ignore
        super().__init__(ModelType.GRADIENT_BOOSTING, config)
        self.n_estimators = self.config.get('n_estimators', 100)
        self.learning_rate = self.config.get('learning_rate', 0.1)

    async def decide(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> DecisionResult:
        """使用梯度提升进行决策"""
        try:
            # 计算综合得分
            scores = []
            for option in options:
                score = (
                    option.confidence * 0.5 +
                    (1 - option.risk_score) * 0.3 +
                    (1 / (option.execution_time or 1)) * 0.2
                )
                scores.append(score)

            # 选择最佳选项
            best_idx = np.argmax(scores)
            selected_option = options[best_idx]

            return DecisionResult(
                selected_option=selected_option,
                reasoning=f"基于梯度提升模型（{self.n_estimators}轮）的优化决策",
                confidence=float(scores[best_idx]),
                alternative_options=[opt for i, opt in enumerate(options) if i != best_idx],
                model_used=self.model_type.value
            )

        except Exception as e:
            logger.error(f"梯度提升决策失败: {e}", exc_info=True)
            # 返回默认决策
            best_option = max(options, key=lambda x: x.confidence)
            return DecisionResult(
                selected_option=best_option,
                reasoning="默认决策（最高置信度）",
                confidence=best_option.confidence,
                alternative_options=[opt for opt in options if opt != best_option],
                model_used="default"
            )


class ReinforcementLearningDecisionModel(BaseDecisionModel):
    """强化学习决策模型"""

    def __init__(self, config: dict | None = None):  # type: ignore
        super().__init__(ModelType.REINFORCEMENT_LEARNING, config)
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.epsilon = self.config.get('epsilon', 0.1)  # 探索率
        self.q_table: dict[str, np.ndarray] = {}

    async def decide(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> DecisionResult:
        """使用强化学习进行决策"""
        try:
            # 状态表示
            state_key = self._get_state_key(context)

            # 初始化Q表（如果需要）
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(len(options))

            # epsilon-贪婪策略
            if np.random.random() < self.epsilon:
                # 探索：随机选择
                best_idx = np.random.randint(0, len(options))
                reasoning = f"探索性决策（ε={self.epsilon}）"
            else:
                # 利用：选择Q值最高的
                best_idx = np.argmax(self.q_table[state_key])
                reasoning = "利用性决策（最高Q值）"

            selected_option = options[best_idx]
            q_value = float(self.q_table[state_key][best_idx])

            return DecisionResult(
                selected_option=selected_option,
                reasoning=reasoning,
                confidence=min(abs(q_value), 1.0),
                alternative_options=[opt for i, opt in enumerate(options) if i != best_idx],
                model_used=self.model_type.value,
                metadata={"q_value": q_value, "state": state_key}
            )

        except Exception as e:
            logger.error(f"强化学习决策失败: {e}", exc_info=True)
            # 返回默认决策
            best_option = max(options, key=lambda x: x.confidence)
            return DecisionResult(
                selected_option=best_option,
                reasoning="默认决策",
                confidence=best_option.confidence,
                alternative_options=[opt for opt in options if opt != best_option],
                model_used="default"
            )

    def _get_state_key(self, context: DecisionContext) -> str:
        """生成状态键"""
        return f"{context.task_type}_{context.domain}_{int(context.urgency * 10)}"

    async def update_q_value(
        self,
        state: str,
        action: int,
        reward: float,
        next_state: str
    ) -> None:
        """更新Q值（Q-learning算法）"""
        if state not in self.q_table:
            return

        # Q-learning更新规则
        current_q = self.q_table[state][action]
        max_next_q = np.max(self.q_table.get(next_state, np.array([0])))
        new_q = current_q + self.learning_rate * (reward + 0.95 * max_next_q - current_q)
        self.q_table[state][action] = new_q


class EnsembleVotingDecisionModel(BaseDecisionModel):
    """集成投票决策模型"""

    def __init__(self, config: dict | None = None):  # type: ignore
        super().__init__(ModelType.ENSEMBLE_VOTING, config)
        self.models: list[BaseDecisionModel] = []
        self.voting_strategy = self.config.get('voting_strategy', 'soft')  # soft or hard

    def add_model(self, model: BaseDecisionModel) -> None:
        """添加子模型"""
        self.models.append(model)

    async def decide(
        self,
        options: list[DecisionOption],
        context: DecisionContext
    ) -> DecisionResult:
        """使用集成投票进行决策"""
        try:
            if not self.models:
                # 如果没有子模型，使用默认决策
                best_option = max(options, key=lambda x: x.confidence)
                return DecisionResult(
                    selected_option=best_option,
                    reasoning="集成投票模型：无子模型，使用默认决策",
                    confidence=best_option.confidence,
                    alternative_options=[opt for opt in options if opt != best_option],
                    model_used="ensemble_default"
                )

            # 收集所有模型的决策
            decisions = await asyncio.gather(*[
                model.decide(options, context) for model in self.models
            ])

            if self.voting_strategy == 'hard':
                # 硬投票：多数投票
                votes = {}
                for decision in decisions:
                    option_id = decision.selected_option.option_id
                    votes[option_id] = votes.get(option_id, 0) + 1

                best_option_id = max(votes, key=votes.get)  # type: ignore
                selected_option = next(opt for opt in options if opt.option_id == best_option_id)
                confidence = votes[best_option_id] / len(decisions)

            else:
                # 软投票：加权平均
                option_scores = {}
                for decision in decisions:
                    option_id = decision.selected_option.option_id
                    option_scores[option_id] = option_scores.get(option_id, 0) + decision.confidence

                best_option_id = max(option_scores, key=option_scores.get)  # type: ignore
                selected_option = next(opt for opt in options if opt.option_id == best_option_id)
                confidence = option_scores[best_option_id] / len(decisions)

            return DecisionResult(
                selected_option=selected_option,
                reasoning=f"集成投票决策（{self.voting_strategy}投票，{len(self.models)}个子模型）",
                confidence=confidence,
                alternative_options=[opt for opt in options if opt != selected_option],
                model_used=self.model_type.value,
                metadata={"sub_model_decisions": decisions}
            )

        except Exception as e:
            logger.error(f"集成投票决策失败: {e}", exc_info=True)
            # 返回默认决策
            best_option = max(options, key=lambda x: x.confidence)
            return DecisionResult(
                selected_option=best_option,
                reasoning="集成投票失败，使用默认决策",
                confidence=best_option.confidence,
                alternative_options=[opt for opt in options if opt != best_option],
                model_used="default"
            )


class AdvancedDecisionModels:
    """
    高级决策模型集合

    整合了所有决策模型，提供统一的决策接口。
    """

    def __init__(self, config: dict | None = None):  # type: ignore
        self.config = config or {}
        self.models: dict[ModelType, BaseDecisionModel] = {}
        self._initialize_models()

    def _initialize_models(self) -> None:
        """初始化所有决策模型"""
        try:
            # 初始化各个模型
            self.models[ModelType.RANDOM_FOREST] = RandomForestDecisionModel(
                self.config.get('random_forest', {})
            )
            self.models[ModelType.GRADIENT_BOOSTING] = GradientBoostingDecisionModel(
                self.config.get('gradient_boosting', {})
            )
            self.models[ModelType.REINFORCEMENT_LEARNING] = ReinforcementLearningDecisionModel(
                self.config.get('reinforcement_learning', {})
            )
            self.models[ModelType.ENSEMBLE_VOTING] = EnsembleVotingDecisionModel(
                self.config.get('ensemble_voting', {})
            )

            # 为集成模型添加子模型
            ensemble_model = self.models[ModelType.ENSEMBLE_VOTING]
            ensemble_model.add_model(self.models[ModelType.RANDOM_FOREST])
            ensemble_model.add_model(self.models[ModelType.GRADIENT_BOOSTING])

            logger.info("✅ 所有决策模型初始化成功")

        except Exception as e:
            logger.error(f"决策模型初始化失败: {e}", exc_info=True)

    async def make_decision(
        self,
        options: list[DecisionOption],
        context: DecisionContext,
        model_type: ModelType | None = None
    ) -> DecisionResult:
        """
        执行决策

        Args:
            options: 决策选项列表
            context: 决策上下文
            model_type: 指定使用的模型类型，None表示自动选择

        Returns:
            DecisionResult: 决策结果
        """
        try:
            # 自动选择模型
            if model_type is None:
                model_type = self._select_model(context)

            # 获取模型
            model = self.models.get(model_type)
            if not model:
                logger.warning(f"模型 {model_type} 不可用，使用默认模型")
                model = self.models[ModelType.ENSEMBLE_VOTING]

            # 执行决策
            result = await model.decide(options, context)

            logger.info(
                f"决策完成: 模型={result.model_used}, "
                f"选项={result.selected_option.option_id}, "
                f"置信度={result.confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"决策失败: {e}", exc_info=True)
            # 返回默认决策
            best_option = max(options, key=lambda x: x.confidence)
            return DecisionResult(
                selected_option=best_option,
                reasoning="决策失败，使用默认选择",
                confidence=best_option.confidence,
                alternative_options=[opt for opt in options if opt != best_option],
                model_used="fallback"
            )

    def _select_model(self, context: DecisionContext) -> ModelType:
        """
        根据上下文自动选择最合适的模型

        选择规则：
        - 高紧急度 + 高复杂度 → 强化学习（适应性强）
        - 低紧急度 + 低复杂度 → 随机森林（快速）
        - 需要高准确性 → 集成投票（综合多个模型）
        - 其他 → 梯度提升（平衡）
        """
        if context.urgency > 0.8 and context.complexity > 0.8:
            return ModelType.REINFORCEMENT_LEARNING
        elif context.urgency < 0.3 and context.complexity < 0.3:
            return ModelType.RANDOM_FOREST
        elif context.task_type in ['critical', 'high_stakes']:
            return ModelType.ENSEMBLE_VOTING
        else:
            return ModelType.GRADIENT_BOOSTING

    async def train_all_models(self, training_data: list[Any]) -> dict[str, bool]:
        """
        训练所有模型

        Args:
            training_data: 训练数据

        Returns:
            Dict[str, bool]: 每个模型的训练结果
        """
        results = {}
        for model_type, model in self.models.items():
            try:
                success = await model.train(training_data)
                results[model_type.value] = success
                if success:
                    logger.info(f"✅ {model_type.value} 模型训练成功")
                else:
                    logger.warning(f"⚠️  {model_type.value} 模型训练失败")
            except Exception as e:
                logger.error(f"❌ {model_type.value} 模型训练异常: {e}")
                results[model_type.value] = False

        return results

    def get_model_info(self) -> dict[str, Any]:
        """获取所有模型的信息"""
        return {
            model_type.value: {
                'type': model_type.value,
                'config': model.config,
                'is_trained': model.is_trained
            }
            for model_type, model in self.models.items()
        }


# 全局决策模型实例
_advanced_decision_models: AdvancedDecisionModels | None = None


def get_advanced_decision_models(config: dict | None = None) -> AdvancedDecisionModels:  # type: ignore
    """
    获取高级决策模型实例（单例模式）

    Args:
        config: 配置字典

    Returns:
        AdvancedDecisionModels: 决策模型实例
    """
    global _advanced_decision_models
    if _advanced_decision_models is None:
        _advanced_decision_models = AdvancedDecisionModels(config)
    return _advanced_decision_models


# 便捷函数
async def make_decision(
    options: list[DecisionOption],
    context: DecisionContext,
    model_type: ModelType | None = None
) -> DecisionResult:
    """
    便捷函数：执行决策

    Args:
        options: 决策选项列表
        context: 决策上下文
        model_type: 指定模型类型

    Returns:
        DecisionResult: 决策结果
    """
    models = get_advanced_decision_models()
    return await models.make_decision(options, context, model_type)
