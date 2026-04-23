"""
Context Budget 管理模块

提供：
- ContextBudgetManager: Token budget 分配与动态调整
- EvidenceTruncator: 证据裁剪算法
- RollbackTrigger: 回滚触发器与降级策略
- TokenEstimator: Token 估算（tiktoken 优先，近似回退）
"""

from .manager import BudgetAllocation, ContextBudgetManager, BudgetMetrics
from .rollback import RollbackDecision, RollbackReason, RollbackTrigger
from .truncation import EvidenceItem, EvidenceTruncator, TruncationResult
from .utils import TokenEstimator

__all__ = [
    "BudgetAllocation",
    "BudgetMetrics",
    "ContextBudgetManager",
    "EvidenceItem",
    "EvidenceTruncator",
    "RollbackDecision",
    "RollbackReason",
    "RollbackTrigger",
    "TokenEstimator",
    "TruncationResult",
]
