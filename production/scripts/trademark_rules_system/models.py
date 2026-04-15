#!/usr/bin/env python3
"""
商标规则数据库模型
Trademark Rules Database Models

定义PostgreSQL表结构和数据模型

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """文档类型枚举"""
    LAW = "法律"
    REGULATION = "行政法规"
    GUIDELINE = "审查指南"
    INTERPRETATION = "司法解释"
    JUDGMENT = "审理指南"
    UNKNOWN = "未知"


class LegalStatus(Enum):
    """法律状态枚举"""
    VALID = "现行有效"
    EXPIRED = "已失效"
    REVISED = "已被修订"
    SUPERSEDED = "已被废止"
    DRAFT = "草案"


@dataclass
class TrademarkNorm:
    """商标法规表"""
    id: str
    name: str
    document_number: str | None
    issuing_authority: str
    issue_date: datetime | None
    effective_date: datetime | None
    status: str
    document_type: str
    file_path: str
    full_text: str
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class TrademarkArticle:
    """商标条款表"""
    id: str
    norm_id: str
    book_name: str | None
    chapter_name: str | None
    section_name: str | None
    article_number: str
    clause_number: str | None
    item_number: str | None
    original_text: str
    hierarchy_path: str | None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class TrademarkVector:
    """商标向量文档表"""
    id: str
    norm_id: str
    chunk_id: int
    text: str
    char_count: int
    embedding_id: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# PostgreSQL表创建SQL
CREATE_TABLES_SQL = """
-- 商标法规表
CREATE TABLE IF NOT EXISTS trademark_norms (
    id VARCHAR(200) PRIMARY KEY,
    name TEXT NOT NULL,
    document_number VARCHAR(500),
    issuing_authority VARCHAR(200),
    issue_date DATE,
    effective_date DATE,
    status VARCHAR(50) DEFAULT '现行有效',
    document_type VARCHAR(100),
    file_path TEXT,
    full_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trademark_norms_status ON trademark_norms(status);
CREATE INDEX IF NOT EXISTS idx_trademark_norms_type ON trademark_norms(document_type);
CREATE INDEX IF NOT EXISTS idx_trademark_norms_authority ON trademark_norms(issuing_authority);
CREATE INDEX IF NOT EXISTS idx_trademark_norms_effective_date ON trademark_norms(effective_date);

-- 商标条款表
CREATE TABLE IF NOT EXISTS trademark_articles (
    id VARCHAR(200) PRIMARY KEY,
    norm_id VARCHAR(200) NOT NULL,
    book_name VARCHAR(200),
    chapter_name VARCHAR(200),
    section_name VARCHAR(200),
    article_number VARCHAR(50),
    clause_number VARCHAR(50),
    item_number VARCHAR(50),
    original_text TEXT NOT NULL,
    hierarchy_path TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_norm_id FOREIGN KEY (norm_id)
        REFERENCES trademark_norms(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trademark_articles_norm_id ON trademark_articles(norm_id);
CREATE INDEX IF NOT EXISTS idx_trademark_articles_article_number ON trademark_articles(article_number);
CREATE INDEX IF NOT EXISTS idx_trademark_articles_hierarchy_path ON trademark_articles(hierarchy_path);

-- 商标向量文档表
CREATE TABLE IF NOT EXISTS trademark_vectors (
    id VARCHAR(200) PRIMARY KEY,
    norm_id VARCHAR(200) NOT NULL,
    chunk_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    embedding_id VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_vector_norm_id FOREIGN KEY (norm_id)
        REFERENCES trademark_norms(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trademark_vectors_norm_id ON trademark_vectors(norm_id);
CREATE INDEX IF NOT EXISTS idx_trademark_vectors_chunk_id ON trademark_vectors(chunk_id);
CREATE INDEX IF NOT EXISTS idx_trademark_vectors_embedding_id ON trademark_vectors(embedding_id);
"""


# Qdrant集合配置
QDRANT_COLLECTION_CONFIG = {
    "collection_name": "trademark_rules",
    "vectors_config": {
        "size": 1024,
        "distance": "Cosine"
    },
    "optimizers_config": {
        "default_segment_number": 4,
        "indexing_threshold": 20000
    },
    "index_params": {
        "hnsw": {
            "m": 16,
            "ef_construct": 200
        }
    }
}


# NebulaGraph空间配置
NEBULA_SPACE_CONFIG = {
    "space_name": "trademark_graph",
    "partition_num": 10,
    "replica_factor": 1,
    "vid_type": "FIXED_STRING(32)",
    "tags": {
        "TrademarkNorm": [
            "name string",
            "document_type string",
            "issuing_authority string",
            "status string"
        ],
        "TrademarkArticle": [
            "article_number string",
            "content string",
            "chapter string"
        ],
        "TrademarkConcept": [
            "name string",
            "category string",
            "description string"
        ]
    },
    "edges": {
        "HAS_ARTICLE": [
            "order int"
        ],
        "REFERS_TO": [],
        "DEFINES": [],
        "RELATES_TO": []
    }
}
