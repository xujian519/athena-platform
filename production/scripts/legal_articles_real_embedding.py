#!/usr/bin/env python3
"""
法律条款真实embedding向量化系统
作者: 小诺·双鱼公主 v4.0.0
日期: 2025-12-28

使用本地优化的nomic-embed-text-v1.5模型进行向量化
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalEmbeddingService:
    """本地embedding服务 - 使用nomic-embed-text-v1.5"""

    def __init__(self, model_path: str = "/Users/xujian/Athena工作平台/models/nomic-embed-text-v1.5"):
        """
        初始化本地embedding模型

        Args:
            model_path: 本地模型路径
        """
        logger.info(f"🔄 加载本地embedding模型: {model_path}")

        # 加载模型（信任远程代码）
        self.model = SentenceTransformer(
            model_path,
            trust_remote_code=True  # 允许加载自定义模型代码
        )
        self.vector_size = self.model.get_sentence_embedding_dimension()

        logger.info("✅ 模型加载成功")
        logger.info("  - 模型: nomic-embed-text-v1.5")
        logger.info(f"  - 向量维度: {self.vector_size}")
        logger.info(f"  - 设备: {self.model.device}")

    def encode_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        编码文本为向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            向量数组 (N, vector_size)
        """
        logger.info(f"🔄 编码 {len(texts)} 个文本...")

        # 生成embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2归一化
        )

        logger.info(f"✅ 编码完成，向量形状: {embeddings.shape}")
        return embeddings


class LegalArticleReVectorizer:
    """法律条款重新向量化器"""

    def __init__(self, model_path: str = "/Users/xujian/Athena工作平台/models/nomic-embed-text-v1.5"):
        """初始化"""
        self.embedding_service = LocalEmbeddingService(model_path)
        self.vector_size = self.embedding_service.vector_size

    def revectorize_articles(self, articles: list[dict]) -> list[dict]:
        """
        使用真实模型重新向量化法律条款

        Args:
            articles: 法律条款列表

        Returns:
            添加了新向量的条款列表
        """
        logger.info(f"🔄 开始重新向量化 {len(articles)} 个条款")

        # 准备文本：组合条款号和内容
        texts = []
        for article in articles:
            # 优化文本表示，提高检索质量
            text = f"{article['law_name']} {article['article_number']} {article['content']}"
            texts.append(text)

        # 生成高质量向量
        logger.info("🔄 使用nomic-embed-text-v1.5生成embeddings...")
        vectors = self.embedding_service.encode_texts(texts, batch_size=32)

        # 更新向量
        for i, article in enumerate(articles):
            article['vector'] = vectors[i].tolist()
            article['embedding_model'] = 'nomic-embed-text-v1.5'
            article['vector_dim'] = self.vector_size

        logger.info(f"✅ 重新向量化完成，向量维度: {self.vector_size}")
        return articles


class QdrantUpdater:
    """Qdrant更新器"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        """初始化"""
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "patent_rules_complete"

    def recreate_collection(self, vector_size: int) -> Any:
        """
        重建collection并导入新向量

        Args:
            vector_size: 新的向量维度
        """
        logger.info(f"🔄 重建collection: {self.collection_name}")

        # 删除旧collection
        try:
            self.client.delete_collection(self.collection_name)
            logger.info("🗑️  已删除旧collection")
        except Exception as e:
            logger.warning(f"⚠️ 删除失败: {e}")

        # 创建新collection
        logger.info(f"✨ 创建新collection (向量维度: {vector_size})")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        logger.info("✅ Collection创建成功")

    def import_articles(self, articles: list[dict], batch_size: int = 100) -> Any:
        """
        批量导入法律条款

        Args:
            articles: 法律条款列表
            batch_size: 批量大小
        """
        logger.info(f"📥 开始导入 {len(articles)} 个条款")

        # 准备points
        points = []
        for idx, article in enumerate(articles):
            payload = {
                "law_id": article.get('law_id', ''),
                "law_name": article.get('law_name', ''),
                "article_number": article.get('article_number', ''),
                "content": article.get('content', ''),
                "chapter": article.get('chapter', ''),
                "section": article.get('section', ''),
                "level": article.get('level', ''),
                "effective_date": article.get('effective_date', ''),
                "source_file": article.get('source_file', ''),
                "word_count": article.get('metadata', {}).get('word_count', 0),
                "char_count": article.get('metadata', {}).get('char_count', 0),
                "embedding_model": article.get('embedding_model', 'unknown'),
                "vectorized_at": datetime.now().isoformat()
            }

            point = PointStruct(
                id=idx,
                vector=article['vector'],
                payload=payload
            )
            points.append(point)

        # 批量上传
        total_batches = (len(points) + batch_size - 1) // batch_size

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = i // batch_size + 1

            logger.info(f"📤 上传批次 {batch_num}/{total_batches} ({len(batch)} points)")
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )

        logger.info("✅ 导入完成")

    def verify_import(self) -> bool:
        """验证导入"""
        logger.info("🔍 验证导入结果")

        info = self.client.get_collection(self.collection_name)
        logger.info("📊 Collection信息:")
        logger.info(f"  - Points数量: {info.points_count}")
        logger.info(f"  - 向量维度: {info.config.params.vectors.size}")
        logger.info(f"  - 距离度量: {info.config.params.vectors.distance}")

        # 测试检索
        logger.info("\n🔍 测试向量检索:")
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=[0.1] * info.config.params.vectors.size,
            limit=3
        )

        for i, result in enumerate(results, 1):
            payload = result.payload
            logger.info(f"\n  {i}. 【{payload.get('law_name', '')}】")
            logger.info(f"     条款: {payload.get('article_number', '')}")
            logger.info(f"     内容: {payload.get('content', '')[:60]}...")
            logger.info(f"     模型: {payload.get('embedding_model', 'unknown')}")
            logger.info(f"     相似度: {result.score:.4f}")


def main() -> None:
    """主函数"""

    # 配置
    json_file = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_articles_20251228_173733.json"
    output_file = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_articles_real_embedding.json"
    model_path = "/Users/xujian/Athena工作平台/models/nomic-embed-text-v1.5"

    # 加载数据
    logger.info(f"📂 加载数据: {json_file}")
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    logger.info(f"✅ 加载 {len(articles)} 个条款")

    # 1. 使用真实模型重新向量化
    revectorizer = LegalArticleReVectorizer(model_path)
    articles = revectorizer.revectorize_articles(articles)

    # 2. 保存新的JSON
    logger.info(f"💾 保存更新后的数据: {output_file}")
    data['articles'] = articles
    data['embedding_model'] = 'nomic-embed-text-v1.5'
    data['vector_dim'] = revectorizer.vector_size
    data['revectorized_at'] = datetime.now().isoformat()

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("✅ 数据保存完成")

    # 3. 重建Qdrant collection
    updater = QdrantUpdater()
    updater.recreate_collection(revectorizer.vector_size)
    updater.import_articles(articles)
    updater.verify_import()

    # 总结
    logger.info(f"\n{'='*60}")
    logger.info("✅ 真实embedding向量化完成!")
    logger.info(f"{'='*60}")
    logger.info("📊 处理统计:")
    logger.info(f"  - 条款数量: {len(articles)}")
    logger.info("  - embedding模型: nomic-embed-text-v1.5")
    logger.info(f"  - 向量维度: {revectorizer.vector_size}")
    logger.info("  - 向量质量: 真实语义向量")
    logger.info("💾 输出文件:")
    logger.info(f"  - 更新JSON: {output_file}")
    logger.info(f"  - 向量库: collection={updater.collection_name}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
