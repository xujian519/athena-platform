#!/usr/bin/env python3
"""
专利规则数据库处理器
Patent Rules Database Processor

高质量处理专利法律文档，包括：
- P0: 专利法、实施细则、审查指南（最高质量）
- P1: 司法解释（高质量）
- P2: 无效复审决定书（中等质量）

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import re

# 添加项目路径
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from psycopg2 import errors as psycopg2_errors
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.embedding.bge_embedding_service import BGEEmbeddingService
from core.reranking.bge_reranker import BGEReranker, RerankConfig, RerankMode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """文档类型"""
    PATENT_LAW = "patent_law"              # 专利法
    IMPLEMENTATION_RULES = "rules"         # 实施细则
    EXAMINATION_GUIDE = "guide"            # 审查指南
    JUDICIAL_INTERPRETATION = "judicial"   # 司法解释
    INVALIDATION_DECISION = "decision"     # 无效决定


class Priority(Enum):
    """处理优先级"""
    P0 = 0  # 核心法律文档（最高质量）
    P1 = 1  # 司法解释（高质量）
    P2 = 2  # 决定书（中等质量）


@dataclass
class PatentRule:
    """专利规则数据结构"""
    id: str                              # 唯一ID
    rule_type: str                       # 规则类型
    source_name: str                     # 来源文档名称
    priority: int                        # 优先级
    hierarchy_path: str                  # 层级路径（如：第一章/第一节/第一条）
    article_number: str | None        # 条款号
    chapter: str | None               # 章节
    section: str | None               # 节
    content: str                         # 规则内容
    keywords: list[str] = field(default_factory=list)  # 关键词
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据
    vector_id: str | None = None      # 向量ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProcessedDocument:
    """处理后的文档"""
    source_file: Path                     # 源文件路径
    doc_type: DocumentType               # 文档类型
    priority: Priority                   # 优先级
    rules: list[PatentRule]              # 提取的规则列表
    total_chars: int = 0                 # 总字符数
    processing_time: float = 0.0          # 处理时间（秒）


class PatentDocumentParser:
    """专利文档解析器"""

    def __init__(self):
        self.stats = {
            'total_documents': 0,
            'total_rules': 0,
            'by_type': {},
            'by_priority': {0: 0, 1: 0, 2: 0}
        }

    def parse_document(
        self,
        file_path: Path,
        doc_type: DocumentType,
        priority: Priority
    ) -> ProcessedDocument:
        """
        解析专利文档

        Args:
            file_path: 文档文件路径
            doc_type: 文档类型
            priority: 优先级

        Returns:
            处理后的文档对象
        """
        start_time = datetime.now()

        # 读取文件内容
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # 根据文档类型选择解析策略
        if doc_type in [DocumentType.PATENT_LAW, DocumentType.IMPLEMENTATION_RULES]:
            rules = self._parse_structured_law(content, file_path.name, doc_type, priority)
        elif doc_type == DocumentType.EXAMINATION_GUIDE:
            rules = self._parse_examination_guide(content, file_path.name, priority)
        elif doc_type == DocumentType.JUDICIAL_INTERPRETATION:
            rules = self._parse_judicial_interpretation(content, file_path.name, priority)
        elif doc_type == DocumentType.INVALIDATION_DECISION:
            rules = self._parse_invalidation_decision(content, file_path.name, priority)
        else:
            rules = []

        processing_time = (datetime.now() - start_time).total_seconds()

        doc = ProcessedDocument(
            source_file=file_path,
            doc_type=doc_type,
            priority=priority,
            rules=rules,
            total_chars=len(content),
            processing_time=processing_time
        )

        # 更新统计
        self.stats['total_documents'] += 1
        self.stats['total_rules'] += len(rules)
        self.stats['by_type'][doc_type.value] = self.stats['by_type'].get(doc_type.value, 0) + 1
        self.stats['by_priority'][priority.value] += len(rules)

        return doc

    def _parse_structured_law(
        self,
        content: str,
        source_name: str,
        doc_type: DocumentType,
        priority: Priority
    ) -> list[PatentRule]:
        """
        解析结构化法律文档（专利法、实施细则）

        支持格式：
        - Markdown格式: ## 章 / ### 节 / #### 条
        - 纯文本格式: 第一条... / 第一章... / 第一节...
        """
        rules = []
        lines = content.split('\n')

        current_chapter = None
        current_section = None
        current_article = None
        current_content = []

        for line in lines:
            line = line.rstrip()

            # 跳过空行和目录
            if not line or line.startswith('目') or '目录' in line:
                continue

            # 检测章节条标题
            # 格式1: Markdown标题
            if line.startswith('#### '):
                # 保存前一条
                if current_article and current_content:
                    rules.append(self._create_rule(
                        source_name, doc_type, priority,
                        current_chapter, current_section,
                        current_article, '\n'.join(current_content)
                    ))

                # 新条款
                current_article = line[4:].strip()
                current_content = []

            elif line.startswith('### '):
                # 节
                if current_article and current_content:
                    rules.append(self._create_rule(
                        source_name, doc_type, priority,
                        current_chapter, current_section,
                        current_article, '\n'.join(current_content)
                    ))
                    current_article = None
                    current_content = []

                current_section = line[3:].strip()

            elif line.startswith('## '):
                # 章
                if current_article and current_content:
                    rules.append(self._create_rule(
                        source_name, doc_type, priority,
                        current_chapter, current_section,
                        current_article, '\n'.join(current_content)
                    ))
                    current_article = None
                    current_content = []

                current_chapter = line[2:].strip()

            # 格式2: 纯文本格式（专利法格式）
            elif re.match(r'^第[一二三四五六七八九十百千零\d]+条', line):
                # 保存前一条
                if current_article and current_content:
                    rules.append(self._create_rule(
                        source_name, doc_type, priority,
                        current_chapter, current_section,
                        current_article, '\n'.join(current_content)
                    ))

                # 新条款
                current_article = line.strip()
                current_content = []

            elif re.match(r'^第[一二三四五六七八九十百千零\d]+章', line):
                # 章
                if current_article and current_content:
                    rules.append(self._create_rule(
                        source_name, doc_type, priority,
                        current_chapter, current_section,
                        current_article, '\n'.join(current_content)
                    ))
                    current_article = None
                    current_content = []

                current_chapter = line.strip()

            elif re.match(r'^第[一二三四五六七八九十百千零\d]+[章节节]', line):
                # 节
                if current_article and current_content:
                    rules.append(self._create_rule(
                        source_name, doc_type, priority,
                        current_chapter, current_section,
                        current_article, '\n'.join(current_content)
                    ))
                    current_article = None
                    current_content = []

                current_section = line.strip()

            elif current_article:
                # 条款内容
                current_content.append(line)

        # 保存最后一条
        if current_article and current_content:
            rules.append(self._create_rule(
                source_name, doc_type, priority,
                current_chapter, current_section,
                current_article, '\n'.join(current_content)
            ))

        return rules

    def _parse_examination_guide(
        self,
        content: str,
        source_name: str,
        priority: Priority
    ) -> list[PatentRule]:
        """
        解析专利审查指南（分块策略）

        按章节分块，每块500-800字
        """
        rules = []
        lines = content.split('\n')

        current_chapter = None
        current_section = None
        current_chunk = []
        current_chunk_size = 0

        for line in lines:
            line = line.rstrip()

            # 检测标题
            if line.startswith('## '):
                # 保存前一块
                if current_chunk:
                    rules.append(self._create_guide_rule(
                        source_name, priority,
                        current_chapter, current_section,
                        '\n'.join(current_chunk)
                    ))
                    current_chunk = []
                    current_chunk_size = 0

                current_chapter = line[2:].strip()
                current_section = None

            elif line.startswith('### '):
                # 保存前一块
                if current_chunk:
                    rules.append(self._create_guide_rule(
                        source_name, priority,
                        current_chapter, current_section,
                        '\n'.join(current_chunk)
                    ))
                    current_chunk = []
                    current_chunk_size = 0

                current_section = line[3:].strip()

            elif line.strip():
                # 内容行
                current_chunk.append(line)
                current_chunk_size += len(line)

                # 达到块大小限制，创建新块
                if current_chunk_size >= 700:
                    rules.append(self._create_guide_rule(
                        source_name, priority,
                        current_chapter, current_section,
                        '\n'.join(current_chunk)
                    ))
                    current_chunk = []
                    current_chunk_size = 0

        # 保存最后一块
        if current_chunk:
            rules.append(self._create_guide_rule(
                source_name, priority,
                current_chapter, current_section,
                '\n'.join(current_chunk)
            ))

        return rules

    def _parse_judicial_interpretation(
        self,
        content: str,
        source_name: str,
        priority: Priority
    ) -> list[PatentRule]:
        """解析司法解释（按条款处理）"""
        # 使用与法律文档相同的解析逻辑
        return self._parse_structured_law(
            content, source_name,
            DocumentType.JUDICIAL_INTERPRETATION,
            priority
        )

    def _parse_invalidation_decision(
        self,
        content: str,
        source_name: str,
        priority: Priority
    ) -> list[PatentRule]:
        """
        解析无效复审决定书（提取摘要）

        提取：决定号、案由、请求人观点、专利权人观点、决定要点
        """
        rules = []

        # 提取决定号
        decision_number = self._extract_decision_number(source_name, content)

        # 提取关键部分
        summary_parts = []

        # 案由
        case_match = re.search(r'一、案由\s*\n(.*?)(?=\n二、|\n【|$)', content, re.DOTALL)
        if case_match:
            summary_parts.append(f"案由：{case_match.group(1).strip()}")

        # 请求人认为
        requester_match = re.search(
            r'二、请求人认为\s*\n(.*?)(?=\n三、|\n专利权人|\n【|$)',
            content, re.DOTALL
        )
        if requester_match:
            summary_parts.append(f"请求人观点：{requester_match.group(1).strip()[:200]}")

        # 决定要点
        decision_match = re.search(
            r'决定[要结论]\s*\n(.*?)(?=\n【|$)',
            content, re.DOTALL
        )
        if decision_match:
            summary_parts.append(f"决定要点：{decision_match.group(1).strip()[:300]}")

        # 创建摘要规则
        if summary_parts:
            rule = PatentRule(
                id=self._generate_id(source_name),
                rule_type=DocumentType.INVALIDATION_DECISION.value,
                source_name=source_name,
                priority=priority.value,
                hierarchy_path=f"决定书/{decision_number}",
                article_number=decision_number,
                chapter=None,
                section=None,
                content='\n'.join(summary_parts),
                keywords=[decision_number, "无效复审"],
                metadata={
                    'decision_number': decision_number,
                    'document_type': 'invalidation_decision'
                }
            )
            rules.append(rule)

        return rules

    def _create_rule(
        self,
        source_name: str,
        doc_type: DocumentType,
        priority: Priority,
        chapter: str | None,
        section: str | None,
        article_number: str,
        content: str
    ) -> PatentRule:
        """创建规则对象"""
        # 提取条款号
        article_num = self._extract_article_number(article_number)

        # 构建层级路径
        hierarchy_parts = []
        if chapter:
            hierarchy_parts.append(chapter)
        if section:
            hierarchy_parts.append(section)
        if article_num:
            hierarchy_parts.append(article_num)
        hierarchy_path = '/'.join(hierarchy_parts)

        # 提取关键词
        keywords = self._extract_keywords(content)

        return PatentRule(
            id=self._generate_id(f"{source_name}_{article_num}"),
            rule_type=doc_type.value,
            source_name=source_name,
            priority=priority.value,
            hierarchy_path=hierarchy_path,
            article_number=article_num,
            chapter=chapter,
            section=section,
            content=content.strip(),
            keywords=keywords,
            metadata={
                'document_type': doc_type.value,
                'article_number': article_num,
                'chapter': chapter,
                'section': section
            }
        )

    def _create_guide_rule(
        self,
        source_name: str,
        priority: Priority,
        chapter: str | None,
        section: str | None,
        content: str
    ) -> PatentRule:
        """创建审查指南规则对象"""
        # 生成块ID
        chunk_id = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]

        # 构建层级路径
        hierarchy_parts = []
        if chapter:
            hierarchy_parts.append(chapter)
        if section:
            hierarchy_parts.append(section)
        hierarchy_path = '/'.join(hierarchy_parts)

        return PatentRule(
            id=self._generate_id(f"{source_name}_{chunk_id}"),
            rule_type=DocumentType.EXAMINATION_GUIDE.value,
            source_name=source_name,
            priority=priority.value,
            hierarchy_path=hierarchy_path,
            article_number=None,
            chapter=chapter,
            section=section,
            content=content.strip(),
            keywords=self._extract_keywords(content),
            metadata={
                'document_type': DocumentType.EXAMINATION_GUIDE.value,
                'chunk_id': chunk_id,
                'chapter': chapter,
                'section': section
            }
        )

    def _extract_article_number(self, text: str) -> str | None:
        """提取条款号"""
        # 匹配 "第一条"、"第1条"、"Article 1" 等
        match = re.search(r'第([一二三四五六七八九十百千零\d]+)条', text)
        if match:
            return match.group(0)
        return None

    def _extract_decision_number(self, filename: str, content: str) -> str:
        """提取决定号"""
        # 从文件名提取
        match = re.search(r'\d+', filename)
        if match:
            return match.group(0)

        # 从内容提取
        match = re.search(r'第(\d+)号', content)
        if match:
            return match.group(0)

        return filename

    def _extract_keywords(self, content: str) -> list[str]:
        """提取关键词"""
        keywords = []

        # 法律关键词
        legal_keywords = [
            '专利', '发明', '实用新型', '外观设计', '申请',
            '审查', '授权', '无效', '复审', '异议',
            '权利要求', '说明书', '优先权', '新颖性',
            '创造性', '实用性', '公开', '驳回'
        ]

        for keyword in legal_keywords:
            if keyword in content:
                keywords.append(keyword)

        return keywords[:10]  # 最多10个关键词

    def _generate_id(self, text: str) -> str:
        """生成唯一ID"""
        return hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()


class PatentRulesStorage:
    """专利规则存储层（PostgreSQL + Qdrant + NebulaGraph）"""

    def __init__(
        self,
        pg_conn,
        qdrant_client: QdrantClient,
        nebula_session
    ):
        """
        初始化存储层

        Args:
            pg_conn: PostgreSQL连接
            qdrant_client: Qdrant客户端
            nebula_session: NebulaGraph会话
        """
        self.pg_conn = pg_conn
        self.qdrant = qdrant_client
        self.nebula = nebula_session
        self.collection_name = "patent_rules"
        self.stats = {
            'pg_inserted': 0,
            'qdrant_inserted': 0,
            'nebula_vertices': 0,
            'nebula_edges': 0
        }

    def initialize_schemas(self) -> Any:
        """初始化数据库Schema"""
        logger.info("初始化数据库Schema...")

        # PostgreSQL表
        self._init_postgres_table()

        # Qdrant集合
        self._init_qdrant_collection()

        # NebulaGraph图空间
        self._init_nebula_graph()

        logger.info("✅ Schema初始化完成")

    def _init_postgres_table(self) -> Any:
        """初始化PostgreSQL表"""
        cursor = self.pg_conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patent_rules (
                id VARCHAR(100) PRIMARY KEY,
                rule_type VARCHAR(50) NOT NULL,
                source_name VARCHAR(500),
                priority INTEGER NOT NULL,
                hierarchy_path TEXT,
                article_number VARCHAR(100),
                chapter VARCHAR(200),
                section VARCHAR(200),
                content TEXT NOT NULL,
                keywords JSONB,
                metadata JSONB,
                vector_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patent_rules_type
            ON patent_rules(rule_type);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patent_rules_priority
            ON patent_rules(priority);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patent_rules_metadata
            ON patent_rules USING GIN(metadata);
        """)

        self.pg_conn.commit()
        logger.info("✅ PostgreSQL表已创建")

        # 单独尝试创建中文全文索引
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patent_rules_content
                ON patent_rules USING GIN(to_tsvector('chinese', content));
            """)
            self.pg_conn.commit()
        except psycopg2_errors.UndefinedObject:
            # 中文配置不存在，尝试使用英文配置
            self.pg_conn.rollback()
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_patent_rules_content
                    ON patent_rules USING GIN(to_tsvector('english', content));
                """)
                self.pg_conn.commit()
                logger.info("ℹ️  使用英文全文索引配置")
            except Exception:
                # 英文配置也不存在或失败，跳过全文索引
                self.pg_conn.rollback()
                logger.warning("⚠️  全文索引创建失败，跳过")

    def _init_qdrant_collection(self) -> Any:
        """初始化Qdrant集合"""
        collections = self.qdrant.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            logger.info(f"✅ Qdrant集合已创建: {self.collection_name}")
        else:
            logger.info(f"ℹ️  Qdrant集合已存在: {self.collection_name}")

    def _init_nebula_graph(self) -> Any:
        """初始化NebulaGraph"""
        # 使用图空间
        self.nebula.execute('USE legaldb;')

        # 创建Tag
        self.nebula.execute("""
            CREATE TAG IF NOT EXISTS PatentRule(
                name string,
                type string,
                content string,
                source string,
                priority int
            );
        """)

        self.nebula.execute("""
            CREATE TAG IF NOT EXISTS PatentDecision(
                decision_number string,
                summary string
            );
        """)

        # 创建Edge
        self.nebula.execute("""
            CREATE EDGE IF NOT EXISTS REFERS_TO(
                reference_type string,
                context string
            );
        """)

        self.nebula.execute("""
            CREATE EDGE IF NOT EXISTS CONTAINS(
                hierarchy_level int
            );
        """)

        self.nebula.execute("""
            CREATE EDGE IF NOT EXISTS BASED_ON(
                legal_basis string
            );
        """)

        logger.info("✅ NebulaGraph Schema已创建")

    def store_rules(
        self,
        rules: list[PatentRule],
        embeddings: np.ndarray
    ) -> int:
        """
        存储规则到三数据库

        Args:
            rules: 规则列表
            embeddings: 向量数组

        Returns:
            成功存储的数量
        """
        stored_count = 0

        for rule, embedding in zip(rules, embeddings, strict=False):
            try:
                # 1. PostgreSQL
                self._store_to_postgres(rule)

                # 2. Qdrant
                self._store_to_qdrant(rule, embedding)

                # 3. NebulaGraph
                self._store_to_nebula(rule)

                stored_count += 1

            except Exception as e:
                logger.error(f"存储失败 {rule.id}: {e}")

        return stored_count

    def _store_to_postgres(self, rule: PatentRule) -> Any:
        """存储到PostgreSQL"""
        cursor = self.pg_conn.cursor()

        cursor.execute("""
            INSERT INTO patent_rules (
                id, rule_type, source_name, priority,
                hierarchy_path, article_number, chapter, section,
                content, keywords, metadata, vector_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                keywords = EXCLUDED.keywords,
                metadata = EXCLUDED.metadata;
        """, (
            rule.id,
            rule.rule_type,
            rule.source_name,
            rule.priority,
            rule.hierarchy_path,
            rule.article_number,
            rule.chapter,
            rule.section,
            rule.content,
            json.dumps(rule.keywords, ensure_ascii=False),
            json.dumps(rule.metadata, ensure_ascii=False),
            rule.vector_id
        ))

        self.pg_conn.commit()
        self.stats['pg_inserted'] += 1

    def _store_to_qdrant(self, rule: PatentRule, embedding: np.ndarray) -> Any:
        """存储到Qdrant"""
        # 生成向量ID
        if not rule.vector_id:
            rule.vector_id = f"{rule.rule_type}_{rule.id}"

        # 创建点
        point = PointStruct(
            id=hash(rule.vector_id) % (2**63),
            vector=embedding.tolist(),
            payload={
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'source': rule.source_name,
                'priority': rule.priority,
                'chapter': rule.chapter or '',
                'article': rule.article_number or '',
                'keywords': rule.keywords,
                'hierarchy_path': rule.hierarchy_path,
                'content_preview': rule.content[:200]
            }
        )

        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        self.stats['qdrant_inserted'] += 1

    def _store_to_nebula(self, rule: PatentRule) -> Any:
        """存储到NebulaGraph"""
        # 生成顶点ID
        vid = f"{rule.rule_type}_{rule.id}"

        # 插入顶点
        if rule.rule_type == DocumentType.INVALIDATION_DECISION.value:
            tag = "PatentDecision"
            # 提前处理字符串转义
            decision_num = rule.article_number or ""
            summary_text = rule.content[:100].replace('"', '\\"') if rule.content else ""
            props = f'decision_number: "{decision_num}", summary: "{summary_text}"'
        else:
            tag = "PatentRule"
            article_or_path = rule.article_number or rule.hierarchy_path
            props = f'name: "{article_or_path}", type: "{rule.rule_type}", source: "{rule.source_name}", priority: {rule.priority}'

        stmt = f'INSERT VERTEX {rule.rule_type}({props}) VALUES "{vid}";'
        try:
            self.nebula.execute(stmt)
            self.stats['nebula_vertices'] += 1
        except Exception:
            pass  # 顶点可能已存在

    def print_stats(self) -> Any:
        """打印存储统计"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 存储统计")
        logger.info("=" * 60)
        logger.info(f"PostgreSQL插入: {self.stats['pg_inserted']}")
        logger.info(f"Qdrant插入: {self.stats['qdrant_inserted']}")
        logger.info(f"NebulaGraph顶点: {self.stats['nebula_vertices']}")
        logger.info(f"NebulaGraph边: {self.stats['nebula_edges']}")
        logger.info("=" * 60 + "\n")


class PatentRulesProcessor:
    """专利规则处理器（主处理器）"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化处理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.source_dir = Path(self.config.get(
            'source_dir',
            '/Users/xujian/Athena工作平台/data/专利'
        ))

        # 初始化解析器
        self.parser = PatentDocumentParser()

        # 初始化嵌入服务（稍后初始化）
        self.embedding_service: BGEEmbeddingService | None = None
        self.reranker: BGEReranker | None = None

        # 存储层（稍后初始化）
        self.storage: PatentRulesStorage | None = None

        # 统计
        self.stats = {
            'total_documents': 0,
            'total_rules': 0,
            'p0_documents': 0,
            'p0_rules': 0,
            'p1_rules': 0,
            'p2_rules': 0,
            'processing_time': 0.0
        }

    async def initialize(self):
        """初始化处理器"""
        logger.info("初始化专利规则处理器...")

        # 初始化嵌入服务
        self.embedding_service = BGEEmbeddingService(
            model_name='bge-m3',
            device='mps',
            batch_size=32
        )
        logger.info("✅ BGE-M3嵌入服务已初始化")

        # 初始化Reranker
        reranker_config = RerankConfig(
            mode=RerankMode.TOP_K_RERANK,
            top_k=100,
            final_top_k=10,
            threshold=0.2,
            batch_size=16
        )
        self.reranker = BGEReranker(
            model_path='/Users/xujian/Athena工作平台/models/converted/bge-reranker-large',
            config=reranker_config
        )
        await self.reranker.initialize_async()
        logger.info("✅ BGE-Reranker已初始化")

        logger.info("✅ 处理器初始化完成")

    def set_storage(self, storage: PatentRulesStorage) -> None:
        """设置存储层"""
        self.storage = storage

    def scan_documents(self) -> dict[Priority, list[tuple[Path, DocumentType]]]:
        """
        扫描源目录，分类文档

        Returns:
            按优先级分组的文档列表
        """
        documents = {Priority.P0: [], Priority.P1: [], Priority.P2: []}

        # P0核心文档
        p0_files = [
            ('中华人民共和国专利法_20201017.md', DocumentType.PATENT_LAW),
            ('中华人民共和国专利法实施细则_20231211.md', DocumentType.IMPLEMENTATION_RULES),
            ('专利审查指南（最新版）.md', DocumentType.EXAMINATION_GUIDE),
        ]

        for filename, doc_type in p0_files:
            file_path = self.source_dir / filename
            if file_path.exists():
                documents[Priority.P0].append((file_path, doc_type))
                logger.info(f"📄 P0文档: {filename}")
            else:
                logger.warning(f"⚠️  文件不存在: {filename}")

        # P1司法解释
        judicial_files = list(self.source_dir.glob("最高法*解释*.md"))
        judicial_files.extend(self.source_dir.glob("司法解释*.md"))
        for file_path in judicial_files:
            documents[Priority.P1].append((file_path, DocumentType.JUDICIAL_INTERPRETATION))

        logger.info(f"📄 P1司法解释: {len(documents[Priority.P1])}个文件")

        # P2决定书
        decision_dir = self.source_dir / "无效复审决定_cleaned"
        if decision_dir.exists():
            decision_files = list(decision_dir.glob("*.md"))[:100]  # 限制100个测试
            for file_path in decision_files:
                documents[Priority.P2].append((file_path, DocumentType.INVALIDATION_DECISION))

            logger.info(f"📄 P2决定书: {len(documents[Priority.P2])}个文件（测试100个）")
        else:
            logger.warning(f"⚠️  目录不存在: {decision_dir}")

        return documents

    async def process_documents(
        self,
        documents: dict[Priority, list[tuple[Path, DocumentType]]],
        priorities: list[Priority] | None = None
    ):
        """
        处理文档

        Args:
            documents: 文档字典
            priorities: 要处理的优先级列表
        """
        if priorities is None:
            priorities = [Priority.P0, Priority.P1, Priority.P2]

        total_start = datetime.now()

        for priority in priorities:
            if priority not in documents:
                continue

            docs = documents[priority]
            logger.info("\n" + "=" * 60)
            logger.info(f"🔄 处理优先级 {priority.name}: {len(docs)}个文档")
            logger.info("=" * 60)

            for file_path, doc_type in tqdm(docs, desc=f"处理{priority.name}"):
                await self._process_single_document(file_path, doc_type, priority)

        self.stats['processing_time'] = (datetime.now() - total_start).total_seconds()

        # 打印统计
        self._print_final_stats()

    async def _process_single_document(
        self,
        file_path: Path,
        doc_type: DocumentType,
        priority: Priority
    ):
        """处理单个文档"""
        try:
            # 解析文档
            processed_doc = self.parser.parse_document(file_path, doc_type, priority)

            if not processed_doc.rules:
                logger.warning(f"⚠️  未提取到规则: {file_path.name}")
                return

            logger.info(f"📄 {file_path.name}: 提取{len(processed_doc.rules)}条规则")

            # 向量化
            texts = [rule.content for rule in processed_doc.rules]
            embeddings = self.embedding_service.encode(texts)

            # 分配向量ID
            for rule, _embedding in zip(processed_doc.rules, embeddings, strict=False):
                rule.vector_id = f"{rule.rule_type}_{rule.id}"

            # 存储
            if self.storage:
                stored = self.storage.store_rules(processed_doc.rules, embeddings)
                logger.info(f"✅ 存储{stored}/{len(processed_doc.rules)}条规则")

            # 更新统计
            self.stats['total_documents'] += 1
            self.stats['total_rules'] += len(processed_doc.rules)

            if priority == Priority.P0:
                self.stats['p0_documents'] += 1
                self.stats['p0_rules'] += len(processed_doc.rules)
            elif priority == Priority.P1:
                self.stats['p1_rules'] += len(processed_doc.rules)
            else:
                self.stats['p2_rules'] += len(processed_doc.rules)

        except Exception as e:
            logger.error(f"❌ 处理失败 {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

    def _print_final_stats(self) -> Any:
        """打印最终统计"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 处理完成统计")
        logger.info("=" * 60)
        logger.info(f"总文档数: {self.stats['total_documents']}")
        logger.info(f"总规则数: {self.stats['total_rules']}")
        logger.info(f"\nP0核心文档: {self.stats['p0_documents']}个文档, {self.stats['p0_rules']}条规则")
        logger.info(f"P1司法解释: {self.stats['p1_rules']}条规则")
        logger.info(f"P2决定书: {self.stats['p2_rules']}条规则")
        logger.info(f"\n总处理时间: {self.stats['processing_time']:.2f}秒")
        logger.info(f"平均速度: {self.stats['total_rules'] / max(self.stats['processing_time'], 1):.1f} 规则/秒")
        logger.info("=" * 60 + "\n")

    async def close(self):
        """关闭处理器"""
        if self.reranker:
            await self.reranker.close_async()
        logger.info("✅ 处理器已关闭")


async def main():
    """主函数"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 专利规则数据库处理器")
    logger.info("=" * 60)

    # 初始化处理器
    processor = PatentRulesProcessor()
    await processor.initialize()

    # 扫描文档
    documents = processor.scan_documents()

    # TODO: 初始化存储层（需要数据库连接）
    # storage = PatentRulesStorage(pg_conn, qdrant_client, nebula_session)
    # storage.initialize_schemas()
    # processor.set_storage(storage)

    # 处理文档
    await processor.process_documents(documents, priorities=[Priority.P0])

    # 关闭处理器
    await processor.close()

    logger.info("✅ 处理完成！")


if __name__ == "__main__":
    asyncio.run(main())
