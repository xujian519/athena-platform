from __future__ import annotations
"""统一评估框架"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    """评估结果"""
    score: float
    metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

class BaseEvaluator(ABC):
    """评估器基类"""

    @abstractmethod
    def evaluate(self, data: Any) -> EvaluationResult:
        """执行评估"""
        pass

class UnifiedEvaluationFramework:
    """统一评估框架"""

    def __init__(self):
        self.evaluators: dict[str, BaseEvaluator] = {}

    def register_evaluator(self, name: str, evaluator: BaseEvaluator):
        """注册评估器"""
        self.evaluators[name] = evaluator

    def evaluate(self, name: str, data: Any) -> EvaluationResult | None:
        """执行评估"""
        if name in self.evaluators:
            return self.evaluators[name].evaluate(data)
        return None
