
"""
法律提示词融合配置。
"""

import os
from dataclasses import dataclass, field


DEFAULT_WIKI_ROOT = (
    "/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库"
)


@dataclass
class WikiConfig:
    root_path: str = os.getenv("LEGAL_WIKI_ROOT", DEFAULT_WIKI_ROOT)
    include_extensions: tuple[str, ...] = (".md",)
    max_file_size_bytes: int = 2 * 1024 * 1024
    snippet_char_limit: int = 1200
    watch_enabled: bool = os.getenv("LEGAL_WIKI_WATCH_ENABLED", "false").lower() == "true"


@dataclass
class FusionDataSources:
    postgres_dsn: str = os.getenv("LEGAL_PG_DSN", "")
    postgres_schema: str = os.getenv("LEGAL_PG_SCHEMA", "public")
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    pg_timeout_seconds: int = int(os.getenv("LEGAL_PG_TIMEOUT_SECONDS", "5"))
    neo4j_timeout_seconds: int = int(os.getenv("LEGAL_NEO4J_TIMEOUT_SECONDS", "5"))


@dataclass
class FusionConfig:
    data_sources: FusionDataSources = field(default_factory=FusionDataSources)
    wiki: WikiConfig = field(default_factory=WikiConfig)
    default_top_k_per_source: int = int(os.getenv("LEGAL_FUSION_TOP_K", "5"))
    max_total_evidence: int = int(os.getenv("LEGAL_FUSION_MAX_EVIDENCE", "12"))
    cache_ttl_seconds: int = int(os.getenv("LEGAL_FUSION_CACHE_TTL", "900"))
    enable_postgres: bool = os.getenv("LEGAL_FUSION_ENABLE_POSTGRES", "true").lower() == "true"
    enable_neo4j: bool = os.getenv("LEGAL_FUSION_ENABLE_NEO4J", "true").lower() == "true"
    enable_wiki: bool = os.getenv("LEGAL_FUSION_ENABLE_WIKI", "true").lower() == "true"
