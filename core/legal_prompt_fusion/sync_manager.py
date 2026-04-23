from __future__ import annotations

"""
Wiki 变更同步与模板版本策略。
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .config import FusionConfig
from .providers import UnifiedLegalKnowledgeRepository


@dataclass
class SyncStatus:
    wiki_revision: str
    indexed_documents: int
    template_version: str
    verified_at: str
    alerts: list[str]


class WikiSyncManager:
    """负责把知识库版本映射到提示词模板版本。"""

    def __init__(
        self,
        repository: Optional[UnifiedLegalKnowledgeRepository] = None,
        config: Optional[FusionConfig] = None,
    ):
        self.config = config or FusionConfig()
        self.repository = repository or UnifiedLegalKnowledgeRepository(self.config)

    def build_sync_status(self, template_family: str = "legal_prompt_fusion") -> SyncStatus:
        revision, count = self.repository.get_wiki_revision()
        template_version = self._template_version(template_family, revision)
        alerts: list[str] = []
        if count == 0:
            alerts.append("wiki 未发现可索引文档")
        return SyncStatus(
            wiki_revision=revision,
            indexed_documents=count,
            template_version=template_version,
            verified_at=datetime.now(timezone.utc).isoformat(),
            alerts=alerts,
        )

    def verify_relevance(self, query: str, context_summary: dict[str, Any]) -> dict[str, Any]:
        revision, count = self.repository.get_wiki_revision()
        missing_dimensions = []
        if not context_summary.get("legal_articles"):
            missing_dimensions.append("legal_articles")
        if not context_summary.get("graph_relations"):
            missing_dimensions.append("graph_relations")
        if not context_summary.get("wiki_background"):
            missing_dimensions.append("wiki_background")
        return {
            "query": query,
            "wiki_revision": revision,
            "indexed_documents": count,
            "missing_dimensions": missing_dimensions,
            "is_valid": len(missing_dimensions) < 3,
        }

    @staticmethod
    def _template_version(template_family: str, revision: str) -> str:
        digest = hashlib.sha256(f"{template_family}:{revision}".encode("utf-8")).hexdigest()
        return f"{template_family}:{digest[:12]}"
