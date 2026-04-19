from __future__ import annotations
"""
综合决策模块
Integrated Decision Module

基于钱学森系统工程思想的综合决策系统
"""

from .integrated_decision_engine import (
    AgentOpinion,
    ConsensusLevel,
    Decision,
    DirectionType,
    IntegratedDecisionEngine,
    IntegrationResult,
    QualitativeDirection,
    get_decision_engine,
    make_integrated_decision,
)

__all__ = [
    "AgentOpinion",
    "ArbitrationDecision",
    "ArbitrationResult",
    "ConflictResolver",
    "ConsensusLevel",
    "Decision",
    "DirectionType",
    "IntegratedDecisionEngine",
    "IntegrationResult",
    "QualitativeDirection",
    "get_decision_engine",
    "make_integrated_decision",
]
