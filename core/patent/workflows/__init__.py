from __future__ import annotations
"""
patent.workflows包
"""

from .analysis_workflow import AnalysisWorkflow, AnalysisWorkflowInput, AnalysisWorkflowResult
from .legal_workflow import LegalWorkflow, LegalWorkflowInput, LegalWorkflowResult
from .search_workflow import SearchWorkflow, SearchWorkflowInput, SearchWorkflowResult

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
