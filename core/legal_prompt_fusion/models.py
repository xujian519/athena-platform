
"""
法律提示词融合通用数据模型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    POSTGRES = "postgres"
    NEO4J = "neo4j"
    WIKI = "wiki"


@dataclass
class RetrievalEvidence:
    source_type: SourceType
    source_id: str
    title: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSnippet:
    headline: str
    summary: str
    citation: str
    source_type: SourceType
    freshness_token: str


@dataclass
class FusedPromptContext:
    user_query: str
    domain: str
    scenario: str
    legal_articles: list[KnowledgeSnippet] = field(default_factory=list)
    graph_relations: list[KnowledgeSnippet] = field(default_factory=list)
    wiki_background: list[KnowledgeSnippet] = field(default_factory=list)
    evidence: list[RetrievalEvidence] = field(default_factory=list)
    freshness: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptGenerationRequest:
    user_query: str
    domain: str = "patent"
    scenario: str = "general"
    additional_context: dict[str, Any] = field(default_factory=dict)
    top_k_per_source: int = 5


@dataclass
class PromptGenerationResult:
    system_prompt: str
    user_prompt: str
    context: FusedPromptContext
    template_version: str
