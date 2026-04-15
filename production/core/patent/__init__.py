"""
patent module - 专利处理核心模块

提供专利分析、检索、法律研究等完整工作流实现。
"""

from __future__ import annotations
from core.patent.workflows import (
    AnalysisWorkflow,
    AnalysisWorkflowInput,
    AnalysisWorkflowResult,
    LegalWorkflow,
    LegalWorkflowInput,
    LegalWorkflowResult,
    SearchWorkflow,
    SearchWorkflowInput,
    SearchWorkflowResult,
)

__all__ = [
    "AnalysisWorkflow",
    "AnalysisWorkflowInput",
    "AnalysisWorkflowResult",
    "SearchWorkflow",
    "SearchWorkflowInput",
    "SearchWorkflowResult",
    "LegalWorkflow",
    "LegalWorkflowInput",
    "LegalWorkflowResult",
]
