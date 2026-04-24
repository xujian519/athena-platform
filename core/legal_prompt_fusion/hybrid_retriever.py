
"""
法律知识混合检索器。
"""

from collections.abc import Iterable
from typing import List, Optional

from .config import FusionConfig
from .models import RetrievalEvidence, SourceType
from .providers import UnifiedLegalKnowledgeRepository


class HybridLegalRetriever:
    """对结构化、图谱和 wiki 知识做融合检索。"""

    def __init__(
        self,
        repository: Optional[UnifiedLegalKnowledgeRepository] = None,
        config: Optional[FusionConfig] = None,
    ):
        self.config = config or FusionConfig()
        self.repository = repository or UnifiedLegalKnowledgeRepository(self.config)
        self.last_source_degradation: list[str] = []

    def retrieve(self, query: str, top_k_per_source: Optional[int] = None) -> List[RetrievalEvidence]:
        bundle = self.repository.retrieve_all(query, top_k_per_source=top_k_per_source)
        self.last_source_degradation = list(bundle.source_degradation)
        all_items = [*bundle.postgres, *bundle.neo4j, *bundle.wiki]
        ranked = sorted(all_items, key=self._ranking_key, reverse=True)
        return ranked[: self.config.max_total_evidence]

    def summarize_source_distribution(self, evidence: Iterable[RetrievalEvidence]) -> dict[str, int]:
        summary = {source.value: 0 for source in SourceType}
        for item in evidence:
            summary[item.source_type.value] += 1
        return summary

    @staticmethod
    def _ranking_key(item: RetrievalEvidence) -> tuple[float, int]:
        source_bias = {
            SourceType.POSTGRES: 0.35,
            SourceType.NEO4J: 0.25,
            SourceType.WIKI: 0.2,
        }
        content_bonus = min(len(item.content) / 1000.0, 0.2)
        return item.score + source_bias.get(item.source_type, 0.0) + content_bonus, len(item.content)