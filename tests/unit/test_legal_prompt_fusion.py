from __future__ import annotations

from pathlib import Path

from core.legal_prompt_fusion.config import FusionConfig, WikiConfig
from core.legal_prompt_fusion.models import (
    PromptGenerationRequest,
    RetrievalEvidence,
    SourceType,
)
from core.legal_prompt_fusion.prompt_context_builder import LegalPromptContextBuilder
from core.legal_prompt_fusion.sync_manager import WikiSyncManager
from core.legal_prompt_fusion.wiki_indexer import ObsidianWikiIndexer


class StubRetriever:
    last_source_degradation: list[str] = []

    def retrieve(self, query: str, top_k_per_source: int | None = None):
        return [
            RetrievalEvidence(
                source_type=SourceType.POSTGRES,
                source_id="pg:article:22",
                title="专利法第二十二条",
                content="发明应当具备新颖性、创造性和实用性。",
                score=0.95,
                metadata={"table": "legal_documents"},
            ),
            RetrievalEvidence(
                source_type=SourceType.NEO4J,
                source_id="neo4j:rule:creativity",
                title="创造性判断关系链",
                content="最接近现有技术 -> 区别特征 -> 技术问题 -> 技术启示。",
                score=0.81,
                metadata={"labels": ["ScenarioRule", "LegalConcept"]},
            ),
            RetrievalEvidence(
                source_type=SourceType.WIKI,
                source_id="wiki:创造性-概述与三步法框架",
                title="创造性-概述与三步法框架",
                content="三步法适用于创造性判断，需结合最接近现有技术与技术启示。",
                score=10.0,
                metadata={"version_hash": "wikihash123"},
            ),
        ]

    @staticmethod
    def summarize_source_distribution(evidence):
        return {
            "postgres": sum(1 for item in evidence if item.source_type == SourceType.POSTGRES),
            "neo4j": sum(1 for item in evidence if item.source_type == SourceType.NEO4J),
            "wiki": sum(1 for item in evidence if item.source_type == SourceType.WIKI),
        }


class StubSyncManager:
    def build_sync_status(self, template_family: str = "legal_prompt_fusion"):
        class Status:
            wiki_revision = "rev-001"
            indexed_documents = 42
            template_version = "legal_prompt_fusion:abc123"
            verified_at = "2026-04-23T00:00:00+00:00"
            alerts = []

        return Status()


def test_wiki_indexer_scan_and_revision(tmp_path: Path):
    vault = tmp_path / "Wiki"
    vault.mkdir(parents=True)
    (vault / "创造性.md").write_text(
        "# 创造性判断\n\n三步法用于创造性分析。\n#专利 #创造性\n",
        encoding="utf-8",
    )
    (vault / "侵权.md").write_text(
        "# 侵权判断\n\n全面覆盖原则用于侵权比对。\n",
        encoding="utf-8",
    )

    indexer = ObsidianWikiIndexer(WikiConfig(root_path=str(tmp_path)))
    documents = indexer.scan()

    assert len(documents) == 2
    assert any(doc.title == "创造性判断" for doc in documents)

    revision = indexer.compute_revision(documents)
    assert revision
    assert len(revision) == 16


def test_sync_manager_builds_template_version_from_wiki_revision(tmp_path: Path):
    vault = tmp_path / "Wiki"
    vault.mkdir(parents=True)
    (vault / "法条.md").write_text("# 法条\n\n专利法第二十二条。", encoding="utf-8")

    config = FusionConfig(wiki=WikiConfig(root_path=str(tmp_path)))
    manager = WikiSyncManager(config=config)
    status = manager.build_sync_status()

    assert status.indexed_documents == 1
    assert status.wiki_revision
    assert status.template_version.startswith("legal_prompt_fusion:")


def test_prompt_context_builder_merges_three_sources():
    builder = LegalPromptContextBuilder(
        retriever=StubRetriever(),
        sync_manager=StubSyncManager(),
    )

    result = builder.build(
        PromptGenerationRequest(
            user_query="请分析该方案是否具备创造性",
            domain="patent",
            scenario="creativity_analysis",
            additional_context={"jurisdiction": "CN"},
            top_k_per_source=3,
        )
    )

    assert "Wiki 修订版本: rev-001" in result.system_prompt
    assert "专利法第二十二条" in result.system_prompt
    assert "创造性判断关系链" in result.system_prompt
    assert "创造性-概述与三步法框架" in result.system_prompt
    assert result.template_version == "legal_prompt_fusion:abc123"
    assert result.context.diagnostics["source_distribution"]["wiki"] == 1
