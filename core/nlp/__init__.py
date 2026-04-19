#!/usr/bin/env python3
from __future__ import annotations
"""
NLP模块
Natural Language Processing Module
"""


from .universal_nlp_provider import (
    NLPProviderType,
    OllamaProvider,
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
    "OllamaProvider",
    "analyze_patent",
    "conversation_response",
    "creative_writing",
    "emotional_analysis",
    "get_nlp_service",
    "technical_reasoning",
]
