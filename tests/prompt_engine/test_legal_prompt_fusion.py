"""
三源融合模块测试

对 Postgres、Neo4j、Wiki 三个知识源分别进行召回、排序与降级验证。
所有外部依赖（psycopg2、neo4j）均通过 mock 隔离。
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.legal_prompt_fusion.config import FusionConfig, FusionDataSources
from core.legal_prompt_fusion.hybrid_retriever import HybridLegalRetriever
from core.legal_prompt_fusion.models import RetrievalEvidence, SourceType
from core.legal_prompt_fusion.providers import (
    Neo4jLegalRepository,
    PostgresLegalRepository,
    UnifiedLegalKnowledgeRepository,
    WikiLegalRepository,
)
import core.legal_prompt_fusion.providers as _lpf_providers


class TestLegalPromptFusion:
    def test_postgres_retrieval(self):
        """Postgres provider 正常召回法律条文。"""
        config = FusionConfig(
            data_sources=FusionDataSources(postgres_dsn="postgresql://test@localhost/legal"),
            enable_postgres=True,
        )
        repo = PostgresLegalRepository(config)

        mock_rows = [
            {
                "source_id": "1",
                "title": "专利法第二十二条",
                "rank": 0.95,
                "content": "发明应当具备新颖性、创造性和实用性。",
            },
        ]

        with patch.object(
            PostgresLegalRepository, "__init__", lambda self, cfg: setattr(self, "config", cfg)
        ):
            pass

        with patch.object(_lpf_providers, "HAS_PSYCOPG2", True, create=True):
            with patch.object(_lpf_providers, "psycopg2", create=True) as mock_psycopg2:
                mock_cursor = MagicMock()
                mock_cursor.fetchall.return_value = mock_rows
                mock_conn = MagicMock()
                mock_conn.__enter__ = MagicMock(return_value=mock_conn)
                mock_conn.__exit__ = MagicMock(return_value=False)
                mock_conn.cursor.return_value.__enter__ = MagicMock(
                    return_value=mock_cursor
                )
                mock_conn.cursor.return_value.__exit__ = MagicMock(
                    return_value=False
                )
                mock_psycopg2.connect.return_value = mock_conn
                mock_psycopg2.extras = MagicMock()
                mock_psycopg2.extras.RealDictCursor = MagicMock()

                results = repo.search("创造性", limit=5)

        assert len(results) == 1
        assert results[0].source_type == SourceType.POSTGRES
        assert results[0].title == "专利法第二十二条"
        assert results[0].score == 0.95
        assert "新颖性" in results[0].content

    def test_neo4j_retrieval(self):
        """Neo4j provider 正常召回图谱关系。"""
        config = FusionConfig(
            data_sources=FusionDataSources(
                neo4j_uri="bolt://localhost:7687",
                neo4j_username="neo4j",
                neo4j_password="test",
            ),
            enable_neo4j=True,
        )
        repo = Neo4jLegalRepository(config)

        # neo4j 返回的是类似 Record 的对象
        mock_record = MagicMock()
        mock_record.get.side_effect = lambda k, default="": {
            "source_id": "neo4j:rule:creativity",
            "title": "创造性判断关系链",
            "content": "最接近现有技术 -> 区别特征 -> 技术问题 -> 技术启示",
            "labels": ["ScenarioRule", "LegalConcept"],
        }.get(k, default)

        with patch.object(_lpf_providers, "HAS_NEO4J", True, create=True):
            with patch.object(
                _lpf_providers, "GraphDatabase", create=True
            ) as mock_graph:
                mock_session = MagicMock()
                mock_session.run.return_value = [mock_record]
                mock_driver = MagicMock()
                mock_driver.session.return_value.__enter__ = MagicMock(
                    return_value=mock_session
                )
                mock_driver.session.return_value.__exit__ = MagicMock(
                    return_value=False
                )
                mock_driver.close = MagicMock()
                mock_graph.driver.return_value = mock_driver

                results = repo.search("创造性", limit=5)

        assert len(results) == 1
        assert results[0].source_type == SourceType.NEO4J
        assert results[0].title == "创造性判断关系链"
        assert results[0].score > 0.0

    def test_wiki_retrieval(self):
        """Wiki provider 正常召回背景知识。"""
        config = FusionConfig(enable_wiki=True)
        repo = WikiLegalRepository(config)

        mock_evidence = [
            RetrievalEvidence(
                source_type=SourceType.WIKI,
                source_id="wiki:创造性-概述与三步法框架",
                title="创造性-概述与三步法框架",
                content="三步法适用于创造性判断，需结合最接近现有技术与技术启示。",
                score=10.0,
                metadata={"version_hash": "wikihash123"},
            )
        ]

        with patch.object(repo.indexer, "search", return_value=mock_evidence):
            results = repo.search("创造性", limit=5)

        assert len(results) == 1
        assert results[0].source_type == SourceType.WIKI
        assert results[0].title == "创造性-概述与三步法框架"
        assert "三步法" in results[0].content

    def test_hybrid_ranking(self):
        """混合排序权重正确：Postgres > Neo4j > Wiki。"""
        config = FusionConfig(max_total_evidence=10)
        retriever = HybridLegalRetriever(config=config)

        evidence = [
            RetrievalEvidence(
                source_type=SourceType.POSTGRES,
                source_id="pg1",
                title="法条",
                content="A" * 500,
                score=0.5,
                metadata={},
            ),
            RetrievalEvidence(
                source_type=SourceType.NEO4J,
                source_id="neo1",
                title="图谱",
                content="B" * 500,
                score=0.5,
                metadata={},
            ),
            RetrievalEvidence(
                source_type=SourceType.WIKI,
                source_id="wiki1",
                title="Wiki",
                content="C" * 500,
                score=0.5,
                metadata={},
            ),
        ]

        pg_key = retriever._ranking_key(evidence[0])
        neo_key = retriever._ranking_key(evidence[1])
        wiki_key = retriever._ranking_key(evidence[2])

        # Postgres bias=0.35, Neo4j=0.25, Wiki=0.2；内容长度相同，故排序固定
        assert pg_key[0] > neo_key[0] > wiki_key[0]

    def test_source_degradation_postgres(self):
        """Postgres 故障时返回空列表，不抛异常。"""
        config = FusionConfig(
            data_sources=FusionDataSources(postgres_dsn="postgresql://bad"),
            enable_postgres=True,
        )
        repo = PostgresLegalRepository(config)

        with patch.object(_lpf_providers, "HAS_PSYCOPG2", True, create=True):
            with patch.object(
                _lpf_providers, "psycopg2", create=True
            ) as mock_psycopg2:
                mock_psycopg2.connect.side_effect = Exception("Connection refused")

                results = repo.search("创造性", limit=5)

        assert results == []

    def test_source_degradation_all(self):
        """三源全故障时返回空结果，系统不崩溃。"""
        config = FusionConfig(
            data_sources=FusionDataSources(
                postgres_dsn="postgresql://bad",
                neo4j_uri="bolt://bad",
            ),
            enable_postgres=True,
            enable_neo4j=True,
            enable_wiki=True,
        )
        repo = UnifiedLegalKnowledgeRepository(config)

        with patch.object(repo.postgres, "search", return_value=[]):
            with patch.object(repo.neo4j, "search", return_value=[]):
                with patch.object(repo.wiki, "search", return_value=[]):
                    bundle = repo.retrieve_all("创造性", top_k_per_source=5)

        assert bundle.postgres == []
        assert bundle.neo4j == []
        assert bundle.wiki == []
