#!/usr/bin/env python3
"""
NLP模块
Natural Language Processing Module
"""


from __future__ import annotations
from .universal_nlp_provider import (
    NLPProviderType,
    MLXProvider,
    TaskType,
    UniversalNLPService,
    analyze_patent,
    conversation_response,
    creative_writing,
    emotional_analysis,
    get_nlp_service,
    technical_reasoning,
)

__all__ = [
    "NLPProviderType",
    "TaskType",
    "UniversalNLPService",
    "MLXProvider",
    "analyze_patent",
    "conversation_response",
    "creative_writing",
    "emotional_analysis",
    "get_nlp_service",
    "technical_reasoning",
]
