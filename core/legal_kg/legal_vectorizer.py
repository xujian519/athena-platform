#!/usr/bin/env python3
from __future__ import annotations
"""
法律文档向量化工具 - 使用BGE-M3模型
将法律文档向量化并存储到Qdrant向量数据库
"""

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))
from legal_kg.legal_text_parser import LegalTextParser

# ==================== 配置 ====================
# BGE-M3模型路径
BGE_M3_MODEL_PATH = "http://127.0.0.1:8766/v1/embeddings"

# PostgreSQL配置
DB_CONFIG = {
    "host": "localhost",
    "port": 15432,
    "database": "phoenix_prod",
    "user": "phoenix_user",
    "password": "phoenix_secure_password_2024",
}

# Qdrant配置
QDRANT_CONFIG = {"host": "localhost", "port": 6333}

# 向量维度(BGE-M3)
VECTOR_DIM = 1024

# 日志配置
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class LawDocument:
    """法律文档数据类"""

    id: int
    title: str
    category: str
    content: str
    importance: str
    file_path: str


class BGEM3Embedding:
    """BGE-M3嵌入模型封装"""

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self) -> Any:
        """加载BGE-M3模型"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"📦 加载BGE-M3模型: {self.model_path}")
            self.model = SentenceTransformer(
                self.model_path, device="mps"  # 使用Apple Silicon GPU加速
            )
            logger.info("✅ BGE-M3模型加载成功")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """批量编码文本为向量"""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,  # 归一化
            )
            return embeddings
        except Exception as e:
            logger.error(f"❌ 编码失败: {e}")
            return np.zeros((len(texts), VECTOR_DIM))


class LegalDocumentVectorizer:
    """法律文档向量化器"""

    # 集合名称配置
    COLLECTIONS = {
        "high_quality": "legal_law_high_quality",  # 高质量:重要法律的条款项
        "medium_quality": "legal_law_medium",  # 中等:普通法律的条文
        "normal": "legal_law_normal",  # 普通:地方法规段落
    }

    def __init__(self, embedding_model: BGEM3Embedding):
        self.embedding_model = embedding_model
        self.qdrant_client = QdrantClient(**QDRANT_CONFIG, check_compatibility=False)
        self.parser = LegalTextParser()
        self.stats = defaultdict(int)

    def create_collections(self) -> Any:
        """创建Qdrant集合"""
        logger.info("📋 创建Qdrant向量集合...")

        collection_configs = {
            "high_quality": {
                "description": "高质量法律文档(民法典等)- 条款项级别",
                "vector_size": VECTOR_DIM,
            },
            "medium_quality": {
                "description": "中等质量法律文档 - 条文级别",
                "vector_size": VECTOR_DIM,
            },
            "normal": {
                "description": "普通法律文档(地方法规)- 段落级别",
                "vector_size": VECTOR_DIM,
            },
        }

        for quality, config in collection_configs.items():
            collection_name = self.COLLECTIONS[quality]

            # 检查是否已存在
            if not self.qdrant_client.collection_exists(collection_name):
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=config["vector_size"], distance=Distance.COSINE
                    ),
                )
                logger.info(f"✅ 创建集合: {collection_name} - {config['description']}")
            else:
                logger.info(f"⊘ 集合已存在: {collection_name}")

    def fetch_documents_from_db(self) -> list[LawDocument]:
        """从PostgreSQL获取法律文档"""
        logger.info("📥 从PostgreSQL获取法律文档...")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    title,
                    category,
                    content,
                    file_path
                FROM legal_documents
                ORDER BY category, id
            """)

            rows = cursor.fetchall()

            documents = []
            for row in rows:
                doc_id, title, category, content, file_path = row

                # 确定重要程度
                importance = self.parser.determine_importance(title)

                documents.append(
                    LawDocument(
                        id=doc_id,
                        title=title,
                        category=category,
                        content=content,
                        importance=importance.value,
                        file_path=file_path,
                    )
                )

            cursor.close()
            conn.close()

            logger.info(f"✅ 获取 {len(documents)} 个法律文档")
            return documents

        except Exception as e:
            logger.error(f"❌ 数据库查询失败: {e}")
            return []

    def vectorize_documents(self, documents: list[LawDocument]) -> Any:
        """向量化文档"""
        logger.info(f"🔄 开始向量化 {len(documents)} 个文档...")

        # 按重要程度分组
        docs_by_importance = defaultdict(list)
        for doc in documents:
            docs_by_importance[doc.importance].append(doc)

        logger.info("📊 文档分布:")
        for importance, docs in docs_by_importance.items():
            logger.info(f"   {importance}: {len(docs)} 个")

        # 处理不同重要程度的文档
        for importance, docs in docs_by_importance.items():
            if importance == "high":
                self._vectorize_high_quality(docs)
            elif importance == "medium":
                self._vectorize_medium_quality(docs)
            else:
                self._vectorize_normal_quality(docs)

        logger.info("\n📊 向量化统计:")
        for key, value in self.stats.items():
            logger.info(f"   {key}: {value}")

    def _vectorize_high_quality(self, documents: list[LawDocument]) -> Any:
        """
        高质量向量化:解析到条款项级别
        用于民法典等重要法律
        """
        logger.info(f"\n🔍 高质量向量化 ({len(documents)} 个文档)...")

        all_points = []
        collection_name = self.COLLECTIONS["high_quality"]

        for doc in documents:
            # 解析法律文本
            parsed = self.parser.parse_law_text(
                content=doc.content, law_id=str(doc.id), title=doc.title
            )

            # 为每一条、款、项生成向量
            for article in parsed.get("articles", []):
                # 条的向量
                article_vector_data = self._create_vector_point(
                    doc_id=doc.id,
                    element_id=article["id"],
                    text=article["content"],
                    metadata={
                        "title": doc.title,
                        "category": doc.category,
                        "level": "article",
                        "article_number": article.get("article_number"),
                        "element_type": "条",
                    },
                )
                if article_vector_data:
                    all_points.append(article_vector_data)
                    self.stats["high_quality_articles"] += 1

                # 款的向量
                for para in article.get("paragraphs", []):
                    para_vector_data = self._create_vector_point(
                        doc_id=doc.id,
                        element_id=para["id"],
                        text=para["content"],
                        metadata={
                            "title": doc.title,
                            "category": doc.category,
                            "level": "paragraph",
                            "article_number": article.get("article_number"),
                            "paragraph_number": para.get("paragraph_number"),
                            "element_type": "款",
                            "parent_id": article["id"],
                        },
                    )
                    if para_vector_data:
                        all_points.append(para_vector_data)
                        self.stats["high_quality_paragraphs"] += 1

            # 项的向量
            for item in parsed.get("items", []):
                item_vector_data = self._create_vector_point(
                    doc_id=doc.id,
                    element_id=item["id"],
                    text=item["content"],
                    metadata={
                        "title": doc.title,
                        "category": doc.category,
                        "level": "item",
                        "element_type": "项",
                        "item_number": item.get("item_number"),
                        "parent_id": item.get("parent_id"),
                    },
                )
                if item_vector_data:
                    all_points.append(item_vector_data)
                    self.stats["high_quality_items"] += 1

            # 批量插入(每100个点)
            if len(all_points) >= 100:
                self._batch_insert(collection_name, all_points)
                all_points = []

        # 插入剩余的点
        if all_points:
            self._batch_insert(collection_name, all_points)

        logger.info("✅ 高质量向量化完成")

    def _vectorize_medium_quality(self, documents: list[LawDocument]) -> Any:
        """中等质量向量化:条文级别"""
        logger.info(f"\n🔍 中等质量向量化 ({len(documents)} 个文档)...")

        all_points = []
        collection_name = self.COLLECTIONS["medium_quality"]

        for doc in documents:
            # 解析法律文本
            parsed = self.parser.parse_law_text(
                content=doc.content, law_id=str(doc.id), title=doc.title
            )

            # 为每一条生成向量
            for article in parsed.get("articles", []):
                vector_data = self._create_vector_point(
                    doc_id=doc.id,
                    element_id=article["id"],
                    text=article["content"],
                    metadata={
                        "title": doc.title,
                        "category": doc.category,
                        "level": "article",
                        "article_number": article.get("article_number"),
                        "element_type": "条",
                    },
                )
                if vector_data:
                    all_points.append(vector_data)
                    self.stats["medium_quality_articles"] += 1

            # 批量插入
            if len(all_points) >= 100:
                self._batch_insert(collection_name, all_points)
                all_points = []

        # 插入剩余的点
        if all_points:
            self._batch_insert(collection_name, all_points)

        logger.info("✅ 中等质量向量化完成")

    def _vectorize_normal_quality(self, documents: list[LawDocument]) -> Any:
        """普通质量向量化:段落级别"""
        logger.info(f"\n🔍 普通质量向量化 ({len(documents)} 个文档)...")

        all_points = []
        collection_name = self.COLLECTIONS["normal"]

        for doc in documents:
            # 简单按段落分割
            paragraphs = doc.content.split("\n\n")

            for i, para in enumerate(paragraphs):
                if len(para.strip()) < 10:
                    continue

                vector_data = self._create_vector_point(
                    doc_id=doc.id,
                    element_id=f"{doc.id}_para_{i}",
                    text=para.strip(),
                    metadata={
                        "title": doc.title,
                        "category": doc.category,
                        "level": "paragraph",
                        "paragraph_number": i,
                        "element_type": "段落",
                    },
                )
                if vector_data:
                    all_points.append(vector_data)
                    self.stats["normal_quality_paragraphs"] += 1

            # 批量插入
            if len(all_points) >= 100:
                self._batch_insert(collection_name, all_points)
                all_points = []

        # 插入剩余的点
        if all_points:
            self._batch_insert(collection_name, all_points)

        logger.info("✅ 普通质量向量化完成")

    def _create_vector_point(
        self, doc_id: int, element_id: str, text: str, metadata: dict
    ) -> PointStruct | None:
        """创建向量点"""
        try:
            # 生成向量
            embedding = self.embedding_model.encode([text])[0]

            # 生成唯一ID(使用哈希)
            point_id = hash(f"{doc_id}_{element_id}")

            return PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "doc_id": doc_id,
                    "element_id": element_id,
                    "text": text[:1000],  # 限制文本长度
                    **metadata,
                },
            )
        except Exception as e:
            logger.warning(f"⚠️ 向量化失败: {e}")
            return None

    def _batch_insert(self, collection_name: str, points: list[PointStruct]) -> Any:
        """批量插入向量点"""
        try:
            self.qdrant_client.upsert(collection_name=collection_name, points=points)
            logger.debug(f"✅ 插入 {len(points)} 个向量到 {collection_name}")
        except Exception as e:
            logger.error(f"❌ 插入失败: {e}")

    def get_statistics(self) -> Any | None:
        """获取向量化统计信息"""
        logger.info("\n📊 Qdrant集合统计:")

        for _quality, collection_name in self.COLLECTIONS.items():
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"📁 {collection_name}:")
                logger.info(f"   向量数量: {collection_info.points_count:,}")
                logger.info(f"   状态: {collection_info.status}")
            except Exception as e:
                logger.warning(f"⚠️ 无法获取 {collection_name} 信息: {e}")


# ==================== 主程序 ====================
def main() -> None:
    """主程序"""
    logger.info("\n" + "=" * 70)
    logger.info("📖 法律文档向量化工具 - BGE-M3")
    logger.info("=" * 70 + "\n")

    # 初始化嵌入模型
    embedding_model = BGEM3Embedding(BGE_M3_MODEL_PATH)

    # 初始化向量化器
    vectorizer = LegalDocumentVectorizer(embedding_model)

    # 创建Qdrant集合
    vectorizer.create_collections()

    # 从数据库获取文档
    documents = vectorizer.fetch_documents_from_db()

    if not documents:
        logger.error("❌ 没有找到法律文档")
        return

    # 向量化文档
    vectorizer.vectorize_documents(documents)

    # 显示统计信息
    vectorizer.get_statistics()

    logger.info("\n✅ 向量化完成!")


if __name__ == "__main__":
    main()
