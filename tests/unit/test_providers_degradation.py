"""
Provider 单源异常自动降级故障注入测试。
"""

from __future__ import annotations

import concurrent.futures
from unittest.mock import MagicMock, patch

import pytest

from core.legal_prompt_fusion.config import FusionConfig
from core.legal_prompt_fusion.models import RetrievalEvidence, SourceType
from core.legal_prompt_fusion.providers import (
    Neo4jLegalRepository,
    PostgresLegalRepository,
    RetrievalBundle,
    UnifiedLegalKnowledgeRepository,
    WikiLegalRepository,
)


class TestPostgresDegradation:
    def test_retrieve_returns_empty_on_search_exception(self):
        repo = PostgresLegalRepository(FusionConfig())
        with patch.object(repo, "search", side_effect=RuntimeError("connection lost")):
            results = repo.retrieve("query", 5)
        assert results == []
        assert repo.is_last_degraded() is True

    def test_retrieve_returns_empty_on_timeout(self):
        repo = PostgresLegalRepository(FusionConfig())
        with patch.object(
            repo, "search", side_effect=lambda *a, **k: concurrent.futures.TimeoutError()
        ):
            # 上面的 side_effect 不会真正抛出 TimeoutError，需要模拟 _TimeoutExecutor.run 抛出
            pass
        # 更直接的 mock：patch _TimeoutExecutor.run
        with patch(
            "core.legal_prompt_fusion.providers._TimeoutExecutor.run",
            side_effect=concurrent.futures.TimeoutError(),
        ):
            results = repo.retrieve("query", 5)
        assert results == []
        assert repo.is_last_degraded() is True

    def test_retrieve_success_clears_degraded(self):
        repo = PostgresLegalRepository(FusionConfig())
        with patch.object(repo, "search", return_value=[]):
            results = repo.retrieve("query", 5)
        assert results == []
        assert repo.is_last_degraded() is False


class TestNeo4jDegradation:
    def test_retrieve_returns_empty_on_search_exception(self):
        repo = Neo4jLegalRepository(FusionConfig())
        with patch.object(repo, "search", side_effect=RuntimeError("connection lost")):
            results = repo.retrieve("query", 5)
        assert results == []
        assert repo.is_last_degraded() is True


class TestWikiDegradation:
    def test_retrieve_returns_empty_on_search_exception(self):
        repo = WikiLegalRepository(FusionConfig())
        with patch.object(repo, "search", side_effect=RuntimeError("index corrupted")):
            results = repo.retrieve("query", 5)
        assert results == []
        assert repo.is_last_degraded() is True


class TestUnifiedRepositoryDegradation:
    """HybridLegalRetriever 级别的故障注入测试。"""

    def _make_evidence(self, source_type: SourceType, title: str) -> RetrievalEvidence:
        return RetrievalEvidence(
            source_type=source_type,
            source_id=f"{source_type.value}:test",
            title=title,
            content="test content",
            score=0.9,
        )

    def test_single_postgres_failure_others_succeed(self):
        """模拟 Postgres 故障：请求成功，融合块含 Neo4j + Wiki 证据。"""
        repo = UnifiedLegalKnowledgeRepository(FusionConfig())
        with patch.object(
            repo.postgres, "search", side_effect=RuntimeError("pg down")
        ):
            with patch.object(
                repo.neo4j,
                "search",
                return_value=[self._make_evidence(SourceType.NEO4J, "neo result")],
            ):
                with patch.object(
                    repo.wiki,
                    "search",
                    return_value=[self._make_evidence(SourceType.WIKI, "wiki result")],
                ):
                    bundle = repo.retrieve_all("query", top_k_per_source=3)

        assert len(bundle.postgres) == 0
        assert len(bundle.neo4j) == 1
        assert len(bundle.wiki) == 1
        assert SourceType.POSTGRES.value in bundle.source_degradation
        assert SourceType.NEO4J.value not in bundle.source_degradation
        assert SourceType.WIKI.value not in bundle.source_degradation

    def test_all_three_sources_failure_returns_empty(self):
        """模拟三源全部故障：请求成功，融合块为空。"""
        repo = UnifiedLegalKnowledgeRepository(FusionConfig())
        with patch.object(
            repo.postgres, "search", side_effect=RuntimeError("pg down")
        ):
            with patch.object(
                repo.neo4j, "search", side_effect=RuntimeError("neo down")
            ):
                with patch.object(
                    repo.wiki, "search", side_effect=RuntimeError("wiki down")
                ):
                    bundle = repo.retrieve_all("query", top_k_per_source=3)

        assert bundle.postgres == []
        assert bundle.neo4j == []
        assert bundle.wiki == []
        assert len(bundle.source_degradation) == 3
        assert SourceType.POSTGRES.value in bundle.source_degradation
        assert SourceType.NEO4J.value in bundle.source_degradation
        assert SourceType.WIKI.value in bundle.source_degradation

    def test_no_failure_no_degradation_recorded(self):
        """全部正常时 source_degradation 为空。"""
        repo = UnifiedLegalKnowledgeRepository(FusionConfig())
        with patch.object(
            repo.postgres,
            "search",
            return_value=[self._make_evidence(SourceType.POSTGRES, "pg")],
        ):
            with patch.object(
                repo.neo4j,
                "search",
                return_value=[self._make_evidence(SourceType.NEO4J, "neo")],
            ):
                with patch.object(
                    repo.wiki,
                    "search",
                    return_value=[self._make_evidence(SourceType.WIKI, "wiki")],
                ):
                    bundle = repo.retrieve_all("query", top_k_per_source=3)

        assert len(bundle.postgres) == 1
        assert len(bundle.neo4j) == 1
        assert len(bundle.wiki) == 1
        assert bundle.source_degradation == []

    def test_single_wiki_failure_others_succeed(self):
        """模拟 Wiki 故障：请求成功，融合块含 Postgres + Neo4j 证据。"""
        repo = UnifiedLegalKnowledgeRepository(FusionConfig())
        with patch.object(
            repo.postgres,
            "search",
            return_value=[self._make_evidence(SourceType.POSTGRES, "pg")],
        ):
            with patch.object(
                repo.neo4j,
                "search",
                return_value=[self._make_evidence(SourceType.NEO4J, "neo")],
            ):
                with patch.object(
                    repo.wiki, "search", side_effect=RuntimeError("wiki down")
                ):
                    bundle = repo.retrieve_all("query", top_k_per_source=3)

        assert len(bundle.postgres) == 1
        assert len(bundle.neo4j) == 1
        assert len(bundle.wiki) == 0
        assert bundle.source_degradation == [SourceType.WIKI.value]
