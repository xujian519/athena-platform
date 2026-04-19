#!/usr/bin/env python3
"""
法律条款BGE-Large-ZH向量化系统
作者: 小诺·双鱼公主 v4.0.0
日期: 2025-12-28

使用本地bge-large-zh-v1.5模型进行高质量向量化
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


class BGEEmbeddingService:
    """BGE-Large-ZH Embedding服务"""

    def __init__(self, model_path: str = "/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5"):
        """
        初始化BGE embedding模型

        Args:
            model_path: 本地模型路径
        """
        logger.info(f"🔄 加载BGE-Large-ZH模型: {model_path}")

        # 加载模型
        self.model = SentenceTransformer(model_path)
        self.vector_size = self.model.get_sentence_embedding_dimension()

        logger.info("✅ BGE模型加载成功")
        logger.info("  - 模型: bge-large-zh-v1.5")
        logger.info(f"  - 向量维度: {self.vector_size}")
        logger.info(f"  - 设备: {self.model.device}")

    def encode_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        编码文本为高质量向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            向量数组 (N, 1024)
        """
        logger.info(f"🔄 BGE编码 {len(texts)} 个文本...")

        # BGE建议的指令格式
        instruction = "为这个句子生成表示以用于检索相关文章："

        # 添加指令前缀
        texts_with_instruction = [instruction + text for text in texts]

        # 生成embeddings
        embeddings = self.model.encode(
            texts_with_instruction,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2归一化
        )

        logger.info(f"✅ BGE编码完成，向量形状: {embeddings.shape}")
        return embeddings


class LegalArticleBGEVectorizer:
    """法律条款BGE向量化器"""

    def __init__(self, model_path: str = "/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5"):
        """初始化"""
        self.bge_service = BGEEmbeddingService(model_path)
        self.vector_size = self.bge_service.vector_size

    def vectorize_articles(self, articles: list[dict]) -> list[dict]:
        """
        使用BGE模型向量化法律条款

        Args:
            articles: 法律条款列表

        Returns:
            添加了BGE向量的条款列表
        """
        logger.info(f"🔄 开始BGE向量化 {len(articles)} 个条款")

        # 准备文本：优化检索质量
        texts = []
        for article in articles:
            # 组合关键信息提高检索质量
            text = f"{article['law_name']}，{article['article_number']}，{article['content']}"
            texts.append(text)

        # 生成高质量BGE向量
        logger.info("🔄 使用bge-large-zh-v1.5生成高质量embeddings...")
        vectors = self.bge_service.encode_texts(texts, batch_size=32)

        # 更新向量
        for i, article in enumerate(articles):
            article['vector'] = vectors[i].tolist()
            article['embedding_model'] = 'bge-large-zh-v1.5'
            article['vector_dim'] = self.vector_size

        logger.info(f"✅ BGE向量化完成，向量维度: {self.vector_size}")
        return articles


class QdrantBGEImporter:
    """Qdrant BGE向量导入器"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        """初始化"""
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "patent_rules_complete"

    def recreate_collection(self, vector_size: int) -> Any:
        """重建collection"""
        logger.info(f"🔄 重建collection: {self.collection_name}")

        # 删除旧collection
        try:
            self.client.delete_collection(self.collection_name)
            logger.info("🗑️  已删除旧collection")
        except Exception as e:
            logger.warning(f"⚠️ 删除失败: {e}")

        # 创建新collection (1024维)
        logger.info(f"✨ 创建新collection (BGE向量: {vector_size}维)")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        logger.info("✅ Collection创建成功")

    def import_articles(self, articles: list[dict], batch_size: int = 100) -> Any:
        """批量导入"""
        logger.info(f"📥 开始导入 {len(articles)} 个条款")

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
                "embedding_model": article.get('embedding_model', 'bge-large-zh-v1.5'),
                "vector_dim": article.get('vector_dim', 1024),
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

    def verify_and_test(self) -> bool:
        """验证并测试检索"""
        logger.info("🔍 验证导入结果")

        info = self.client.get_collection(self.collection_name)
        logger.info("📊 Collection信息:")
        logger.info(f"  - Points数量: {info.points_count}")
        logger.info(f"  - 向量维度: {info.config.params.vectors.size}")
        logger.info(f"  - 距离度量: {info.config.params.vectors.distance}")

        # 测试检索
        logger.info("\n🔍 测试语义检索:")

        # 构造测试查询
        test_queries = [
            "专利授予的条件",
            "发明专利的新颖性",
            "专利权的保护期限"
        ]

        for query in test_queries:
            logger.info(f"\n查询: {query}")

            # 使用BGE编码查询
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5")
            instruction = "为这个句子生成表示以用于检索相关文章："
            query_vector = model.encode(
                instruction + query,
                normalize_embeddings=True
            )

            # 检索 (使用推荐API)
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist(),
                limit=3
            ).points

            for i, result in enumerate(results, 1):
                payload = result.payload
                logger.info(f"  {i}. {payload.get('article_number', '')}")
                logger.info(f"     内容: {payload.get('content', '')[:50]}...")
                logger.info(f"     相似度: {result.score:.4f}")


def main() -> None:
    """主函数"""

    # 配置
    json_file = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_articles_20251228_173733.json"
    output_file = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_articles_bge_embedding.json"

    # 加载数据
    logger.info(f"📂 加载数据: {json_file}")
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    logger.info(f"✅ 加载 {len(articles)} 个条款")

    # 1. BGE向量化
    vectorizer = LegalArticleBGEVectorizer()
    articles = vectorizer.vectorize_articles(articles)

    # 2. 保存数据
    logger.info(f"💾 保存BGE向量化数据: {output_file}")
    data['articles'] = articles
    data['embedding_model'] = 'bge-large-zh-v1.5'
    data['vector_dim'] = vectorizer.vector_size
    data['vectorized_at'] = datetime.now().isoformat()
    data['quality'] = 'high_quality_semantic'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("✅ 数据保存完成")

    # 3. 导入Qdrant
    importer = QdrantBGEImporter()
    importer.recreate_collection(vectorizer.vector_size)
    importer.import_articles(articles)
    importer.verify_and_test()

    # 总结
    logger.info(f"\n{'='*60}")
    logger.info("✅ BGE-Large-ZH向量化完成!")
    logger.info(f"{'='*60}")
    logger.info("📊 处理统计:")
    logger.info(f"  - 条款数量: {len(articles)}")
    logger.info("  - embedding模型: bge-large-zh-v1.5 (BAAI)")
    logger.info(f"  - 向量维度: {vectorizer.vector_size}")
    logger.info("  - 向量质量: 高质量语义向量")
    logger.info("  - 检索能力: 优秀的语义理解")
    logger.info("💾 输出文件:")
    logger.info(f"  - BGE数据: {output_file}")
    logger.info(f"  - 向量库: {importer.collection_name}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
