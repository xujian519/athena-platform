#!/usr/bin/env python3
"""
增强推理基础模块
Enhanced Reasoning Base Module

提供双系统推理和高级推理所需的基础类型和类。
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """推理类型"""

    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    BAYESIAN = "bayesian"
    INTUITIVE = "intuitive"
    ANALYTICAL = "analytical"
    FUZZY = "fuzzy"
    PROBABILISTIC = "probabilistic"
    MODAL = "modal"
    QUALITATIVE = "qualitative"
    COUNTERFACTUAL = "counterfactual"


class ThinkingMode(Enum):
    """思考模式"""

    SYSTEM1 = "system1"  # 快速直觉
    SYSTEM2 = "system2"  # 深度分析
    DUAL = "dual"  # 双系统协同


class ReasoningComplexity(Enum):
    """推理复杂度"""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"


class MetacognitiveState(Enum):
    """元认知状态"""

    EXPLORING = "exploring"
    ANALYZING = "analyzing"
    VERIFYING = "verifying"
    REFLECTING = "reflecting"
    CONFIDENT = "confident"


@dataclass
class ReasoningStep:
    """推理步骤"""

    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    step_number: int = 0
    description: str = ""
    reasoning_type: ReasoningType = ReasoningType.ANALYTICAL
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    # 扩展字段 - 用于高级推理
    input_state: dict[str, Any] = field(default_factory=dict)
    output_state: dict[str, Any] = field(default_factory=dict)
    operation: str = ""
    justification: str = ""
    computation_time: float = 0.0


@dataclass
class ReasoningContext:
    """推理上下文"""

    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = "general"
    complexity: ReasoningComplexity = ReasoningComplexity.MEDIUM
    thinking_mode: ThinkingMode = ThinkingMode.DUAL
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[ReasoningStep] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    """推理结果"""

    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conclusion: str = ""
    reasoning_chain: list[ReasoningStep] | ReasoningChain = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    success: bool = True
    error_message: str = ""
    reasoning_type: ReasoningType | None = None
    performance_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """推理链"""

    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: list[ReasoningStep] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    final_confidence: float = 0.0
    total_time: float = 0.0
    completed_at: float = 0.0
    reasoning_type: ReasoningType | None = None

    def add_step(self, step: ReasoningStep) -> None:
        """添加推理步骤"""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)

    def get_total_time(self) -> float:
        """获取总时间"""
        if self.completed_at > 0:
            return self.completed_at - self.start_time
        elif self.end_time > 0:
            return self.end_time - self.start_time
        return self.total_time


def create_reasoning_step(
    step_number: int,
    description: str,
    reasoning_type: ReasoningType = ReasoningType.ANALYTICAL,
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
    confidence: float = 0.0,
    operation: str | None = None,
    input_state: dict[str, Any] | None = None,
    output_state: dict[str, Any] | None = None,
    justification: str | None = None,
    computation_time: float = 0.0,
) -> ReasoningStep:
    """创建推理步骤"""
    return ReasoningStep(
        step_number=step_number,
        description=description,
        reasoning_type=reasoning_type,
        input_data=input_data or {},
        output_data=output_data or {},
        confidence=confidence,
        operation=operation or "",
        input_state=input_state or {},
        output_state=output_state or {},
        justification=justification or "",
        computation_time=computation_time,
    )


class BaseReasoner:
    """基础推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.reasoner_id = str(uuid.uuid4())
        self.reasoning_history: list[ReasoningResult] = []

    async def reason(self, query: str, context: ReasoningContext = None) -> ReasoningResult:
        """执行推理

        Args:
            query: 推理查询
            context: 推理上下文

        Returns:
            推理结果
        """
        raise NotImplementedError("子类必须实现此方法")

    def get_history(self) -> list[ReasoningResult]:
        """获取推理历史"""
        return self.reasoning_history

    def clear_history(self) -> None:
        """清空推理历史"""
        self.reasoning_history.clear()


class MetacognitiveMonitor:
    """元认知监控器"""

    def __init__(self):
        self.state = MetacognitiveState.EXPLORING
        self.confidence_history: list[float] = []
        self.reasoning_steps: list[ReasoningStep] = []

    def update_state(self, new_state: MetacognitiveState) -> None:
        """更新元认知状态"""
        self.state = new_state
        logger.debug(f"元认知状态更新: {new_state.value}")

    def record_confidence(self, confidence: float) -> Any:
        """记录置信度"""
        self.confidence_history.append(confidence)

    def get_average_confidence(self) -> float:
        """获取平均置信度"""
        if not self.confidence_history:
            return 0.0
        return sum(self.confidence_history) / len(self.confidence_history)

    def should_continue_reasoning(self) -> bool:
        """判断是否应该继续推理"""
        if self.state == MetacognitiveState.CONFIDENT:
            return False
        if self.get_average_confidence() > 0.85:
            return False
        return not len(self.reasoning_steps) > 10


class ReasoningStrategySelector:
    """推理策略选择器"""

    def __init__(self):
        self.strategies = {
            ReasoningComplexity.SIMPLE: [ReasoningType.DEDUCTIVE, ReasoningType.INTUITIVE],
            ReasoningComplexity.MEDIUM: [ReasoningType.INDUCTIVE, ReasoningType.ABDUCTIVE],
            ReasoningComplexity.COMPLEX: [ReasoningType.ANALOGICAL, ReasoningType.CAUSAL],
            ReasoningComplexity.EXPERT: [ReasoningType.BAYESIAN, ReasoningType.ANALYTICAL],
        }

    def select_strategy(
        self, complexity: ReasoningComplexity, context: ReasoningContext = None
    ) -> list[ReasoningType]:
        """选择推理策略"""
        return self.strategies.get(complexity, [ReasoningType.ANALYTICAL])


def create_reasoning_context(
    domain: str = "general",
    complexity: ReasoningComplexity = ReasoningComplexity.MEDIUM,
    thinking_mode: ThinkingMode = ThinkingMode.DUAL,
) -> ReasoningContext:
    """创建推理上下文"""
    return ReasoningContext(domain=domain, complexity=complexity, thinking_mode=thinking_mode)


# 导出所有类型和类
__all__ = [
    "BaseReasoner",
    "MetacognitiveMonitor",
    "MetacognitiveState",
    "ReasoningChain",
    "ReasoningComplexity",
    "ReasoningContext",
    "ReasoningResult",
    "ReasoningStep",
    "ReasoningStrategySelector",
    "ReasoningType",
    "ThinkingMode",
    "create_reasoning_context",
    "create_reasoning_step",
]
