#!/usr/bin/env python3
from __future__ import annotations
"""
决策引擎配置类
Decision Engine Configuration

集中管理决策引擎的所有硬编码配置参数

作者: Athena AI系统
创建时间: 2025-12-25
版本: 1.0.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DecisionLayer(Enum):
    """决策层级枚举"""

    INSTINCT = "instinct"  # 本能直觉
    EMOTIONAL = "emotional"  # 情感感知
    LOGICAL = "logical"  # 逻辑分析
    STRATEGIC = "strategic"  # 战略思考
    ETHICAL = "ethical"  # 伦理判断
    COLLABORATIVE = "collaborative"  # 协作智慧


@dataclass
class DecisionConfig:
    """
    决策引擎配置类

    集中管理所有决策相关的配置参数,便于维护和调整
    """

    # 层级权重配置
    layer_weights: dict[DecisionLayer, float] = field(
        default_factory=lambda: {
            DecisionLayer.INSTINCT: 0.10,  # 本能直觉
            DecisionLayer.EMOTIONAL: 0.25,  # 情感感知(小诺核心)
            DecisionLayer.LOGICAL: 0.20,  # 逻辑分析
            DecisionLayer.STRATEGIC: 0.15,  # 战略思考
            DecisionLayer.ETHICAL: 0.15,  # 伦理判断
            DecisionLayer.COLLABORATIVE: 0.15,  # 协作智慧
        }
    )

    # 学习参数
    learning_rate: float = 0.1

    # 内存管理参数
    decision_history_maxlen: int = 1000
    experience_base_maxlen: int = 10000

    # 性能指标初始值
    initial_performance_metrics: dict[str, float] = field(
        default_factory=lambda: {
            "total_decisions": 0,
            "successful_decisions": 0,
            "average_confidence": 0.0,
            "decision_speed": 0.0,
            "learning_effectiveness": 0.0,
            "emotional_satisfaction": 0.0,
        }
    )

    # 决策阈值
    confidence_threshold: float = 0.5
    urgency_threshold: float = 0.7

    def validate(self) -> bool:
        """验证配置参数的有效性"""
        # 检查权重总和
        total_weight = sum(self.layer_weights.values())
        if not (0.99 <= total_weight <= 1.01):  # 允许小的浮点误差
            raise ValueError(f"层级权重总和应为1.0,当前为{total_weight}")

        # 检查学习率范围
        if not (0.0 < self.learning_rate <= 1.0):
            raise ValueError(f"学习率应在(0, 1]范围内,当前为{self.learning_rate}")

        # 检查内存限制
        if self.decision_history_maxlen <= 0:
            raise ValueError(f"决策历史最大长度必须大于0,当前为{self.decision_history_maxlen}")

        if self.experience_base_maxlen <= 0:
            raise ValueError(f"经验库最大长度必须大于0,当前为{self.experience_base_maxlen}")

        # 检查阈值范围
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError(f"置信度阈值应在[0, 1]范围内,当前为{self.confidence_threshold}")

        if not (0.0 <= self.urgency_threshold <= 1.0):
            raise ValueError(f"紧急度阈值应在[0, 1]范围内,当前为{self.urgency_threshold}")

        return True

    def get_layer_weight(self, layer: DecisionLayer) -> float:
        """获取指定层级的权重"""
        return self.layer_weights.get(layer, 0.0)

    def update_layer_weight(self, layer: DecisionLayer, weight: float) -> None:
        """更新指定层级的权重"""
        if not (0.0 <= weight <= 1.0):
            raise ValueError(f"权重必须在[0, 1]范围内,当前为{weight}")
        self.layer_weights[layer] = weight
        self.validate()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "layer_weights": {layer.value: weight for layer, weight in self.layer_weights.items()},
            "learning_rate": self.learning_rate,
            "decision_history_maxlen": self.decision_history_maxlen,
            "experience_base_maxlen": self.experience_base_maxlen,
            "initial_performance_metrics": self.initial_performance_metrics,
            "confidence_threshold": self.confidence_threshold,
            "urgency_threshold": self.urgency_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecisionConfig":
        """从字典创建配置对象"""
        config = cls()

        # 恢复层级权重
        if "layer_weights" in data:
            config.layer_weights = {
                DecisionLayer(key): value for key, value in data.get("layer_weights").items()
            }

        # 恢复其他参数
        for key in [
            "learning_rate",
            "decision_history_maxlen",
            "experience_base_maxlen",
            "confidence_threshold",
            "urgency_threshold",
        ]:
            if key in data:
                setattr(config, key, data.get(key))

        return config


# 默认配置实例
default_config = DecisionConfig()
