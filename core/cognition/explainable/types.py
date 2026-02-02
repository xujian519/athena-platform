#!/usr/bin/env python3
"""
可解释认知模块 - 数据模型
Explainable Cognition Module - Data Models

定义推理过程中使用的数据结构

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ReasoningStepType(Enum):
    """推理步骤类型"""

    INPUT_PROCESSING = "input_processing"
    EVIDENCE_GATHERING = "evidence_gathering"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    INFERENCE = "inference"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    DECISION = "decision"
    EXPLANATION = "explanation"


class FactorImportance(Enum):
    """因子重要性级别"""

    CRITICAL = 5  # 关键因子
    HIGH = 4  # 高重要性
    MEDIUM = 3  # 中等重要性
    LOW = 2  # 低重要性
    MINIMAL = 1  # 最小重要性


@dataclass
class ReasoningStep:
    """推理步骤"""

    step_id: str
    step_type: ReasoningStepType
    description: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    confidence: float
    timestamp: datetime
    execution_time: float
    factors: list["DecisionFactor"] = field(default_factory=list)
    parent_steps: list[str] = field(default_factory=list)
    child_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "description": self.description,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "factors": [f.to_dict() for f in self.factors],
            "parent_steps": self.parent_steps,
            "child_steps": self.child_steps,
        }


@dataclass
class DecisionFactor:
    """决策因子"""

    factor_id: str
    name: str
    description: str
    importance: FactorImportance
    weight: float  # 0.0-1.0
    value: Any
    source: str  # 因子来源 (user_input, knowledge_base, inference, etc.)
    uncertainty: float = 0.0  # 不确定性 0.0-1.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "factor_id": self.factor_id,
            "name": self.name,
            "description": self.description,
            "importance": self.importance.value,
            "weight": self.weight,
            "value": str(self.value),  # 转换为字符串以便序列化
            "source": self.source,
            "uncertainty": self.uncertainty,
        }


@dataclass
class ReasoningPath:
    """推理路径"""

    path_id: str
    query: str
    start_time: datetime
    end_time: datetime | None = None
    steps: list[ReasoningStep] = field(default_factory=list)
    final_decision: dict[str, Any] | None = None
    overall_confidence: float = 0.0
    explanation: str = ""

    def add_step(self, step: ReasoningStep) -> None:
        """添加推理步骤"""
        self.steps.append(step)

        # 建立父子关系
        if len(self.steps) > 1:
            step.parent_steps.append(self.steps[-2].step_id)
            self.steps[-2].child_steps.append(step.step_id)

    def get_total_execution_time(self) -> float:
        """获取总执行时间"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return sum(step.execution_time for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "path_id": self.path_id,
            "query": self.query,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [step.to_dict() for step in self.steps],
            "final_decision": self.final_decision,
            "overall_confidence": self.overall_confidence,
            "explanation": self.explanation,
            "total_execution_time": self.get_total_execution_time(),
        }
