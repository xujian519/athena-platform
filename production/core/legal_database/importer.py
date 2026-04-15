#!/usr/bin/env python3
"""
法律数据库导入器
Legal Database Importer

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

实现"同一源"生成策略:
1. PostgreSQL: 保存权威的结构化信息和版本控制(质量基准)
2. Qdrant: 保存文本块的语义检索能力
3. Neo4j: 在 DB 基础之上叠加实体关系和推理路径 (TD-001: 从NebulaGraph迁移)
"""

from __future__ import annotations
import logging
import uuid
from pathlib import Path
from typing import Any

from tqdm import tqdm

from core.legal_database.parser import LegalTextParser, ParsedArticle, ParsedNorm

logger = logging.getLogger(__name__)


class LegalDatabaseImporter:
    """法律数据库导入器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化导入器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 解析器
        self.parser = LegalTextParser(config)

        # 数据库连接(延迟初始化)
        self.pg_conn = None
        self.pg_cursor = None
        self.qdrant_client = None
        self.nebula_client = None

        # 统计信息
        self.stats = {
            "total_files": 0,
            "imported_norms": 0,
            "imported_articles": 0,
            "imported_vectors": 0,
            "failed_files": 0,
        }

    def connect_postgresql(self, connection_params: dict[str, Any]) -> bool:
        """连接PostgreSQL"""
        try:
            import psycopg2

            self.pg_conn = psycopg2.connect(**connection_params)
            self.pg_cursor = self.pg_conn.cursor()

            # 初始化表结构
            self._init_postgresql_tables()

            logger.info("✅ PostgreSQL连接成功")
            return True

        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            return False

    def connect_qdrant(self, url: str = "http://localhost:6333") -> bool:
        """连接Qdrant"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self.qdrant_client = QdrantClient(url=url)

            # 创建集合
            try:
                self.qdrant_client.create_collection(
                    collection_name="legal_articles",
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                )
                logger.info("✅ Qdrant集合已创建")
            except Exception as e:
                if "already exists" not in str(e):
                    raise e
                logger.info("ℹ️  Qdrant集合已存在")

            logger.info("✅ Qdrant连接成功")
            return True

        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            return False

    def connect_nebula(self, config: dict[str, Any]) -> bool:
        """
        连接Neo4j (TD-001: 从NebulaGraph迁移)

        Args:
            config: Neo4j配置
                {
                    'uri': 'bolt://localhost:7687',
                    'username': 'neo4j',
                    'password': 'password',
                    'database': 'legaldb'
                }

        Returns:
            是否连接成功
        """
        try:
            # TD-001: 使用Neo4j版本的图构建器
            from core.legal_database.neo4j_graph_builder import Neo4jLegalKnowledgeGraphBuilder

            self.neo4j_client = Neo4jLegalKnowledgeGraphBuilder(config)

            # 尝试连接
            if self.neo4j_client.connect():
                logger.info("✅ Neo4j连接成功")
                # 兼容层: 保留nebula_client引用
                self.nebula_client = self.neo4j_client
                return True
            else:
                logger.warning("⚠️  Neo4j连接失败")
                return False

        except Exception as e:
            logger.warning(f"⚠️  Neo4j连接失败(可选): {e}")
            return False

    def _init_postgresql_tables(self) -> Any:
        """初始化PostgreSQL表结构"""
        # 1. 法规表 (LegalNorm)
        self.pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS legal_norms (
                id VARCHAR(200) PRIMARY KEY,
                name TEXT NOT NULL,
                document_number VARCHAR(500),
                issuing_authority VARCHAR(200),
                issue_date DATE,
                effective_date DATE,
                status VARCHAR(50) DEFAULT '现行有效',
                hierarchy VARCHAR(50),
                latest_version_id VARCHAR(200),
                category VARCHAR(100),
                file_path TEXT,
                full_text TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),

                CONSTRAINT fk_latest_version FOREIGN KEY (latest_version_id)
                    REFERENCES legal_norms(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_legal_norms_status ON legal_norms(status);
            CREATE INDEX IF NOT EXISTS idx_legal_norms_hierarchy ON legal_norms(hierarchy);
            CREATE INDEX IF NOT EXISTS idx_legal_norms_category ON legal_norms(category);
            CREATE INDEX IF NOT EXISTS idx_legal_norms_effective_date ON legal_norms(effective_date);
        """)

        # 2. 条款表 (ArticleClause)
        self.pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS legal_clauses (
                id VARCHAR(200) PRIMARY KEY,
                norm_id VARCHAR(200) NOT NULL,
                book_name VARCHAR(200),
                chapter_name VARCHAR(200),
                section_name VARCHAR(200),
                article_number VARCHAR(50),
                clause_number VARCHAR(50),
                item_number VARCHAR(50),
                original_text TEXT NOT NULL,
                effective_date DATE,
                expiry_date DATE,
                hierarchy_path TEXT,
                created_at TIMESTAMP DEFAULT NOW(),

                CONSTRAINT fk_norm_id FOREIGN KEY (norm_id)
                    REFERENCES legal_norms(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_legal_clauses_norm_id ON legal_clauses(norm_id);
            CREATE INDEX IF NOT EXISTS idx_legal_clauses_article_number ON legal_clauses(article_number);
            CREATE INDEX IF NOT EXISTS idx_legal_clauses_hierarchy_path ON legal_clauses(hierarchy_path);
        """)

        # 3. 版本变更表 (NormChange)
        self.pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS legal_norm_changes (
                id VARCHAR(200) PRIMARY KEY,
                norm_id VARCHAR(200) NOT NULL,
                change_type VARCHAR(50) NOT NULL,
                change_basis VARCHAR(200),
                change_date DATE,
                effective_date DATE,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT NOW(),

                CONSTRAINT fk_change_norm_id FOREIGN KEY (norm_id)
                    REFERENCES legal_norms(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_legal_norm_changes_norm_id ON legal_norm_changes(norm_id);
            CREATE INDEX IF NOT EXISTS idx_legal_norm_changes_type ON legal_norm_changes(change_type);
        """)

        self.pg_conn.commit()
        logger.info("✅ PostgreSQL表结构已创建")

    def import_from_directory(
        self,
        data_dir: Path,
        batch_size: int = 100,
        limit: int | None = None,
        categories: list[str] | None = None,
    ):
        """
        从目录导入法律文件

        Args:
            data_dir: 法律数据目录
            batch_size: 批处理大小
            limit: 限制导入数量(用于测试)
            categories: 类别过滤
        """
        logger.info(f"\n{'='*60}")
        logger.info("🚀 开始导入法律数据库")
        logger.info(f"📁 数据目录: {data_dir}")
        logger.info(f"{'='*60}\n")

        # 扫描文件
        all_files = []
        for category_dir in data_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("."):
                category = category_dir.name
                if categories and category not in categories:
                    continue

                for file_path in category_dir.glob("*.md"):
                    all_files.append((file_path, category))

        self.stats["total_files"] = len(all_files)

        if limit:
            all_files = all_files[:limit]

        logger.info(f"📄 待处理文件: {len(all_files)}个")

        # 批量处理
        for i in range(0, len(all_files), batch_size):
            batch = all_files[i : i + batch_size]

            for file_path, category in tqdm(batch, desc=f"批次 {i//batch_size + 1}"):
                try:
                    # 解析文件
                    parsed_norm = self.parser.parse_file(file_path, category)
                    if not parsed_norm:
                        continue

                    # 导入到数据库
                    self._import_norm(parsed_norm)

                    self.stats["imported_norms"] += 1

                except Exception as e:
                    logger.error(f"❌ 导入失败 {file_path.name}: {e}")
                    self.stats["failed_files"] += 1

            # 每批次提交一次
            self.pg_conn.commit()

        # 打印统计
        self._print_final_stats()

    def _import_norm(self, parsed_norm: ParsedNorm) -> Any:
        """导入单个法规"""
        # 1. 插入法规元数据
        self.pg_cursor.execute(
            """
            INSERT INTO legal_norms
            (id, name, document_number, issuing_authority, issue_date, effective_date,
             status, hierarchy, category, file_path, full_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                document_number = EXCLUDED.document_number,
                issuing_authority = EXCLUDED.issuing_authority,
                issue_date = EXCLUDED.issue_date,
                effective_date = EXCLUDED.effective_date,
                status = EXCLUDED.status,
                full_text = EXCLUDED.full_text
        """,
            (
                parsed_norm.id,
                parsed_norm.name,
                parsed_norm.document_number,
                parsed_norm.issuing_authority,
                parsed_norm.issue_date,
                parsed_norm.effective_date,
                parsed_norm.status,
                parsed_norm.hierarchy,
                parsed_norm.category,
                parsed_norm.file_path,
                parsed_norm.full_text[:10000],  # 限制长度
            ),
        )

        # 2. 插入条款
        for _chapter_name, articles in parsed_norm.chapters.items():
            for article in articles:
                for clause_idx, clause in enumerate(article.clauses):
                    clause_id = f"{parsed_norm.id}_{article.article_number}_c{clause_idx}"

                    self.pg_cursor.execute(
                        """
                        INSERT INTO legal_clauses
                        (id, norm_id, chapter_name, section_name, article_number,
                         original_text, hierarchy_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            original_text = EXCLUDED.original_text
                    """,
                        (
                            clause_id,
                            parsed_norm.id,
                            article.chapter_name,
                            article.section_name,
                            article.article_number,
                            clause["text"][:5000],  # 限制长度
                            article.hierarchy_path,
                        ),
                    )

                    self.stats["imported_articles"] += 1

                    # 3. 向量化并导入Qdrant(如果已连接)
                    if self.qdrant_client:
                        self._vectorize_and_import(
                            parsed_norm, article, clause_idx, clause["text"], clause_id
                        )

        self.stats["imported_norms"] += 1

    def _vectorize_and_import(
        self,
        parsed_norm: ParsedNorm,
        article: ParsedArticle,
        clause_idx: int,
        clause_text: str,
        clause_id: str,
    ):
        """向量化并导入到Qdrant"""
        try:
            from qdrant_client.models import PointStruct

            from core.nlp.bge_m3_loader import load_bge_m3_model

            # 延迟加载模型
            if not hasattr(self, "bge_m3_loader"):
                self.bge_m3_loader = load_bge_m3_model()

            # 创建增强文本
            embedding_text = self.parser.create_embedding_text(
                parsed_norm, article, clause_idx, clause_text
            )

            # 生成向量
            embedding = self.bge_m3_loader.encode_single(embedding_text, normalize=True)

            # 创建点
            point = PointStruct(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, clause_id).int % (2**63),
                vector=embedding.tolist(),
                payload={
                    "clause_id": clause_id,
                    "norm_id": parsed_norm.id,
                    "norm_name": parsed_norm.name,
                    "article_number": article.article_number,
                    "chapter_name": article.chapter_name or "",
                    "section_name": article.section_name or "",
                    "hierarchy_path": article.hierarchy_path,
                    "original_text": clause_text[:500],
                    "is_valid": parsed_norm.status == "现行有效",
                    "category": parsed_norm.category or "",
                },
            )

            # 批量收集(稍后上传)
            if not hasattr(self, "qdrant_points"):
                self.qdrant_points = []

            self.qdrant_points.append(point)

            # 每100个点上传一次
            if len(self.qdrant_points) >= 100:
                self.qdrant_client.upsert(
                    collection_name="legal_articles", points=self.qdrant_points
                )
                self.qdrant_points = []

        except Exception as e:
            logger.warning(f"⚠️  向量化失败 {clause_id}: {e}")

    def _print_final_stats(self) -> Any:
        """打印最终统计"""
        # 上传剩余的点
        if hasattr(self, "qdrant_points") and self.qdrant_points:
            self.qdrant_client.upsert(collection_name="legal_articles", points=self.qdrant_points)
            self.stats["imported_vectors"] = len(self.qdrant_points)

        logger.info(f"\n{'='*60}")
        logger.info("📊 法律数据库导入完成")
        logger.info(f"{'='*60}")
        logger.info(f"📁 总文件数: {self.stats['total_files']}")
        logger.info(f"✅ 成功导入: {self.stats['imported_norms']}个法规")
        logger.info(f"📄 导入条款: {self.stats['imported_articles']}条")
        logger.info(f"🔽 导入向量: {self.stats.get('imported_vectors', 0)}个")
        logger.info(f"❌ 导入失败: {self.stats['failed_files']}个")
        logger.info(
            f"📈 成功率: {(self.stats['imported_norms']/max(self.stats['total_files'],1)*100):.1f}%"
        )
        logger.info(f"{'='*60}\n")

    def close(self) -> Any:
        """关闭连接"""
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
