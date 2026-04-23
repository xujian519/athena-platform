
"""
多源法律知识访问层。

提供 Postgres / Neo4j / Wiki 三源检索能力，支持单源异常自动降级：
- 任一源故障时返回空列表，记录 source_degradation，不抛错
- 三源全部故障时正常返回空 evidence 列表
- 默认 200ms 超时，可通过 LEGAL_FUSION_SOURCE_TIMEOUT_MS 环境变量调整
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
from dataclasses import dataclass, field

from .config import FusionConfig
from .models import RetrievalEvidence, SourceType
from .wiki_indexer import ObsidianWikiIndexer

logger = logging.getLogger(__name__)

_DEFAULT_SOURCE_TIMEOUT_MS = int(os.getenv("LEGAL_FUSION_SOURCE_TIMEOUT_MS", "200"))
_DEFAULT_SOURCE_TIMEOUT_SECONDS = _DEFAULT_SOURCE_TIMEOUT_MS / 1000.0

try:
    import psycopg2
    import psycopg2.extras

    HAS_PSYCOPG2 = True
except ImportError:  # pragma: no cover - 依赖缺失时降级
    HAS_PSYCOPG2 = False

try:
    from neo4j import GraphDatabase

    HAS_NEO4J = True
except ImportError:  # pragma: no cover - 依赖缺失时降级
    HAS_NEO4J = False


@dataclass
class RetrievalBundle:
    postgres: list[RetrievalEvidence]
    neo4j: list[RetrievalEvidence]
    wiki: list[RetrievalEvidence]
    source_degradation: list[str] = field(default_factory=list)


class _TimeoutExecutor:
    """内部辅助类：在线程池中执行可调用对象并施加超时。"""

    _executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=8, thread_name_prefix="fusion_source_"
    )

    @classmethod
    def run(cls, fn, timeout_seconds: float, *args, **kwargs):
        future = cls._executor.submit(fn, *args, **kwargs)
        return future.result(timeout=timeout_seconds)


class _DegradableMixin:
    """为 provider 提供降级状态追踪能力。"""

    source_type: SourceType
    _last_degraded: bool = False

    def is_last_degraded(self) -> bool:
        return self._last_degraded

    def _mark_degraded(self, exc: Exception) -> None:
        self._last_degraded = True
        logger.warning(
            "%s 降级: %s (%s)",
            self.source_type.value,
            type(exc).__name__,
            exc,
        )

    def _clear_degraded(self) -> None:
        self._last_degraded = False


class PostgresLegalRepository(_DegradableMixin):
    source_type = SourceType.POSTGRES

    def __init__(self, config: FusionConfig):
        self.config = config

    def search(self, query: str, limit: int) -> list[RetrievalEvidence]:
        if not self.config.enable_postgres or not self.config.data_sources.postgres_dsn or not HAS_PSYCOPG2:
            return []

        sql = """
        SELECT
            COALESCE(id::text, md5(COALESCE(title, '') || COALESCE(content, ''))) AS source_id,
            COALESCE(title, article_title, '未命名法律条目') AS title,
            LEFT(COALESCE(content, article_text, summary, ''), 2000) AS content,
            ts_rank_cd(
                to_tsvector('simple', COALESCE(title, '') || ' ' || COALESCE(content, article_text, summary, '')),
                websearch_to_tsquery('simple', %(query)s)
            ) AS rank
        FROM legal_documents
        WHERE to_tsvector('simple', COALESCE(title, '') || ' ' || COALESCE(content, article_text, summary, ''))
              @@ websearch_to_tsquery('simple', %(query)s)
        ORDER BY rank DESC
        LIMIT %(limit)s
        """

        try:
            with psycopg2.connect(
                self.config.data_sources.postgres_dsn,
                connect_timeout=self.config.data_sources.pg_timeout_seconds,
            ) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(sql, {"query": query, "limit": limit})
                    rows = cursor.fetchall()
        except Exception as exc:
            logger.warning("PostgreSQL 检索失败: %s", exc)
            return []

        results: list[RetrievalEvidence] = []
        for row in rows:
            results.append(
                RetrievalEvidence(
                    source_type=SourceType.POSTGRES,
                    source_id=str(row["source_id"]),
                    title=str(row["title"]),
                    content=str(row["content"]),
                    score=float(row.get("rank") or 0.0),
                    metadata={"backend": "postgres", "table": "legal_documents"},
                )
            )
        return results

    def retrieve(self, query: str, top_k: int) -> list[RetrievalEvidence]:
        """带超时与异常捕获的检索入口。

        失败时返回空列表并记录 source_degradation。
        """
        self._clear_degraded()
        try:
            return _TimeoutExecutor.run(
                self.search, _DEFAULT_SOURCE_TIMEOUT_SECONDS, query, top_k
            )
        except concurrent.futures.TimeoutError as exc:
            self._mark_degraded(exc)
            return []
        except Exception as exc:
            self._mark_degraded(exc)
            return []


class Neo4jLegalRepository(_DegradableMixin):
    source_type = SourceType.NEO4J

    def __init__(self, config: FusionConfig):
        self.config = config

    def search(self, query: str, limit: int) -> list[RetrievalEvidence]:
        if not self.config.enable_neo4j or not HAS_NEO4J:
            return []

        cypher = """
        MATCH (n)
        WHERE any(key IN ['title', 'name', 'article_title', 'content', 'description']
                  WHERE toString(n[key]) CONTAINS $query)
        RETURN
            COALESCE(n.rule_id, n.article_id, n.case_id, elementId(n)) AS source_id,
            COALESCE(n.title, n.name, n.article_title, '未命名图谱节点') AS title,
            LEFT(COALESCE(n.content, n.description, ''), 2000) AS content,
            labels(n) AS labels
        LIMIT $limit
        """

        try:
            driver = GraphDatabase.driver(
                self.config.data_sources.neo4j_uri,
                auth=(
                    self.config.data_sources.neo4j_username,
                    self.config.data_sources.neo4j_password,
                ),
            )
            with driver.session(database=self.config.data_sources.neo4j_database) as session:
                rows = list(session.run(cypher, query=query, limit=limit))
            driver.close()
        except Exception as exc:
            logger.warning("Neo4j 检索失败: %s", exc)
            return []

        results: list[RetrievalEvidence] = []
        for row in rows:
            content = str(row.get("content") or "")
            title = str(row.get("title") or "未命名图谱节点")
            score = min(1.0, 0.4 + 0.01 * max(content.lower().count(query.lower()), 1))
            results.append(
                RetrievalEvidence(
                    source_type=SourceType.NEO4J,
                    source_id=str(row.get("source_id")),
                    title=title,
                    content=content,
                    score=score,
                    metadata={"backend": "neo4j", "labels": row.get("labels", [])},
                )
            )
        return results

    def retrieve(self, query: str, top_k: int) -> list[RetrievalEvidence]:
        """带超时与异常捕获的检索入口。

        失败时返回空列表并记录 source_degradation。
        """
        self._clear_degraded()
        try:
            return _TimeoutExecutor.run(
                self.search, _DEFAULT_SOURCE_TIMEOUT_SECONDS, query, top_k
            )
        except concurrent.futures.TimeoutError as exc:
            self._mark_degraded(exc)
            return []
        except Exception as exc:
            self._mark_degraded(exc)
            return []


class WikiLegalRepository(_DegradableMixin):
    source_type = SourceType.WIKI

    def __init__(self, config: FusionConfig):
        self.config = config
        self.indexer = ObsidianWikiIndexer(config.wiki)

    def search(self, query: str, limit: int) -> list[RetrievalEvidence]:
        if not self.config.enable_wiki:
            return []
        return self.indexer.search(query=query, limit=limit)

    def scan_revision(self) -> tuple[str, int]:
        documents = self.indexer.scan()
        return self.indexer.compute_revision(documents), len(documents)

    def retrieve(self, query: str, top_k: int) -> list[RetrievalEvidence]:
        """带超时与异常捕获的检索入口。

        失败时返回空列表并记录 source_degradation。
        """
        self._clear_degraded()
        try:
            return _TimeoutExecutor.run(
                self.search, _DEFAULT_SOURCE_TIMEOUT_SECONDS, query, top_k
            )
        except concurrent.futures.TimeoutError as exc:
            self._mark_degraded(exc)
            return []
        except Exception as exc:
            self._mark_degraded(exc)
            return []


class UnifiedLegalKnowledgeRepository:
    def __init__(self, config: FusionConfig | None = None):
        self.config = config or FusionConfig()
        self.postgres = PostgresLegalRepository(self.config)
        self.neo4j = Neo4jLegalRepository(self.config)
        self.wiki = WikiLegalRepository(self.config)

    def retrieve_all(self, query: str, top_k_per_source: int | None = None) -> RetrievalBundle:
        limit = top_k_per_source or self.config.default_top_k_per_source

        pg_results = self.postgres.retrieve(query, limit)
        neo_results = self.neo4j.retrieve(query, limit)
        wiki_results = self.wiki.retrieve(query, limit)

        source_degradation: list[str] = []
        if self.postgres.is_last_degraded():
            source_degradation.append(SourceType.POSTGRES.value)
        if self.neo4j.is_last_degraded():
            source_degradation.append(SourceType.NEO4J.value)
        if self.wiki.is_last_degraded():
            source_degradation.append(SourceType.WIKI.value)

        return RetrievalBundle(
            postgres=pg_results,
            neo4j=neo_results,
            wiki=wiki_results,
            source_degradation=source_degradation,
        )

    def get_wiki_revision(self) -> tuple[str, int]:
        return self.wiki.scan_revision()
