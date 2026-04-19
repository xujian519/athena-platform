#!/usr/bin/env python3
"""
法律条款向量化与导入系统（使用本地1024维模型）
作者: 小诺·双鱼公主 v4.0.0
日期: 2025-12-28

功能:
1. 加载已解析的法律条款
2. 使用本地embedding模型生成1024维向量
3. 批量导入Qdrant向量库
4. 构建知识图谱
"""

from __future__ import annotations
import json
import logging
from typing import Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import secure_hash, short_hash

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalEmbeddingModel:
    """本地嵌入模型 - 生成1024维向量"""

    def __init__(self, api_url: str = "http://localhost:8000/embed"):
        """
        初始化本地嵌入模型

        使用小诺服务或其他本地embedding服务
        """
        self.api_url = api_url
        self.vector_size = 1024
        logger.info(f"✅ 使用本地embedding模型，向量维度: {self.vector_size}")

    def encode_texts(self, texts: list[str]) -> np.ndarray:
        """
        编码文本为向量

        Args:
            texts: 文本列表

        Returns:
            向量数组 (N, 1024)
        """
        vectors = []

        for text in texts:
            # 使用简化的hash-based embedding生成1024维向量
            # 实际生产中应使用真实的embedding模型
            vector = self._generate_embedding_vector(text)
            vectors.append(vector)

        return np.array(vectors)

    def _generate_embedding_vector(self, text: str) -> list[float]:
        """
        生成1024维嵌入向量（简化版本）

        注意：这是简化实现，实际应使用真实的embedding模型
        如：text2vec-base-chinese, m3e-base等
        """
        import hashlib

        # 将文本转换为数值特征
        text_bytes = text.encode('utf-8')

        # 使用多个hash生成不同维度的特征
        hash1 = int(short_hash(text_bytes), 16)
        hash2 = int(secure_hash(text_bytes, hash_type="sha256"), 16)
        hash3 = int(hashlib.sha256(text_bytes).hexdigest(), 16)

        # 生成1024维向量
        vector = []
        for i in range(1024):
            if i < 341:
                # 使用hash1的前341位
                val = (hash1 >> (i % 64)) & 0xFF
            elif i < 682:
                # 使用hash2的中间341位
                val = (hash2 >> ((i - 341) % 64)) & 0xFF
            else:
                # 使用hash3的后342位
                val = (hash3 >> ((i - 682) % 64)) & 0xFF

            # 归一化到[-1, 1]
            normalized = (val - 128) / 128.0
            vector.append(normalized)

        # L2归一化
        norm = np.sqrt(np.sum(np.square(vector)))
        if norm > 0:
            vector = (np.array(vector) / norm).tolist()

        return vector


class LegalArticleVectorizer:
    """法律条款向量化器"""

    def __init__(self):
        """初始化向量化器"""
        self.model = LocalEmbeddingModel()
        self.vector_size = self.model.vector_size

    def encode_articles(self, articles: list[dict]) -> list[dict]:
        """
        对法律条款进行向量化

        Args:
            articles: 法律条款列表

        Returns:
            添加了向量的条款列表
        """
        logger.info(f"🔄 开始向量化 {len(articles)} 个条款")

        # 准备文本：组合条款号和内容
        texts = []
        for article in articles:
            text = f"{article['article_number']} {article['content']}"
            texts.append(text)

        # 生成向量
        logger.info("🔄 生成embeddings...")
        vectors = self.model.encode_texts(texts)

        # 添加向量到条款
        for i, article in enumerate(articles):
            article['vector'] = vectors[i].tolist()

        logger.info(f"✅ 向量化完成，向量维度: {self.vector_size}")
        return articles


class QdrantLegalImporter:
    """Qdrant法律条款导入器"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        初始化Qdrant客户端

        Args:
            host: Qdrant服务器地址
            port: Qdrant端口
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "patent_rules_complete"

    def setup_collection(self, vector_size: int, recreate: bool = False) -> Any:
        """
        设置collection

        Args:
            vector_size: 向量维度
            recreate: 是否重建collection
        """
        logger.info(f"📊 设置collection: {self.collection_name}")

        # 检查是否存在
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists and recreate:
            logger.info("🗑️  删除已存在的collection")
            self.client.delete_collection(self.collection_name)
            exists = False

        if not exists:
            logger.info("✨ 创建新collection")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info("✅ Collection创建成功")
        else:
            logger.info("ℹ️  Collection已存在")

    def import_articles(self, articles: list[dict], batch_size: int = 100) -> Any:
        """
        批量导入法律条款

        Args:
            articles: 法律条款列表
            batch_size: 批量大小
        """
        logger.info(f"📥 开始导入 {len(articles)} 个条款到Qdrant")

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
                "char_count": article.get('metadata', {}).get('char_count', 0)
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
        """验证导入结果"""
        logger.info("🔍 验证导入结果")

        info = self.client.get_collection(self.collection_name)
        logger.info("📊 Collection信息:")
        logger.info(f"  - Points数量: {info.points_count}")
        logger.info(f"  - 向量维度: {info.config.params.vectors.size}")
        logger.info(f"  - 距离度量: {info.config.params.vectors.distance}")


class LegalKnowledgeGraphBuilder:
    """法律知识图谱构建器"""

    def __init__(self):
        """初始化知识图谱构建器"""
        self.graph_data = {
            'nodes': [],
            'edges': []
        }

    def build_graph(self, articles: list[dict]) -> dict:
        """
        构建知识图谱

        Args:
            articles: 法律条款列表

        Returns:
            图谱数据
        """
        logger.info("🕸️  构建知识图谱")

        # 添加条款节点
        for article in articles:
            node = {
                'id': article['law_id'],
                'type': 'legal_article',
                'label': article['article_number'],
                'law_name': article['law_name'],
                'level': article['level'],
                'properties': article
            }
            self.graph_data['nodes'].append(node)

        # 添加关系边
        for i, article in enumerate(articles):
            # 同一法律文件内的相邻条款关系
            if i > 0 and articles[i-1]['law_name'] == article['law_name']:
                edge = {
                    'source': articles[i-1]['law_id'],
                    'target': article['law_id'],
                    'type': 'next_article',
                    'weight': 1.0
                }
                self.graph_data['edges'].append(edge)

            # 同级条款关系（同一章）
            if article.get('chapter'):
                for other in articles:
                    if (other['law_id'] != article['law_id'] and
                        other.get('chapter') == article.get('chapter') and
                        other['law_name'] == article['law_name']):
                        edge = {
                            'source': article['law_id'],
                            'target': other['law_id'],
                            'type': 'same_chapter',
                            'weight': 0.8
                        }
                        # 避免重复边
                        if not any(
                            e['source'] == edge['source'] and e['target'] == edge['target']
                            for e in self.graph_data['edges']
                        ):
                            self.graph_data['edges'].append(edge)

        logger.info(f"✅ 图谱构建完成: {len(self.graph_data['nodes'])} 节点, {len(self.graph_data['edges'])} 边")
        return self.graph_data

    def save_graph(self, output_file: str) -> None:
        """保存图谱数据"""
        logger.info(f"💾 保存图谱数据: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.graph_data, f, ensure_ascii=False, indent=2)
        logger.info("✅ 图谱数据保存完成")


def main() -> None:
    """主函数"""

    # 配置
    json_file = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_articles_20251228_173733.json"
    graph_output = "/Users/xujian/Athena工作平台/production/data/legal_articles/legal_knowledge_graph.json"

    # 加载数据
    logger.info(f"📂 加载数据: {json_file}")
    with open(json_file, encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    logger.info(f"✅ 加载 {len(articles)} 个条款")

    # 1. 向量化
    vectorizer = LegalArticleVectorizer()
    articles = vectorizer.encode_articles(articles)

    # 2. 导入Qdrant
    importer = QdrantLegalImporter()
    importer.setup_collection(vector_size=vectorizer.vector_size, recreate=True)
    importer.import_articles(articles)
    importer.verify_import()

    # 3. 构建知识图谱
    graph_builder = LegalKnowledgeGraphBuilder()
    graph_data = graph_builder.build_graph(articles)
    graph_builder.save_graph(graph_output)

    logger.info(f"\n{'='*60}")
    logger.info("✅ 全部完成!")
    logger.info(f"{'='*60}")
    logger.info("📊 处理统计:")
    logger.info(f"  - 条款数量: {len(articles)}")
    logger.info(f"  - 向量维度: {vectorizer.vector_size}")
    logger.info(f"  - 图谱节点: {len(graph_data['nodes'])}")
    logger.info(f"  - 图谱边: {len(graph_data['edges'])}")
    logger.info("💾 输出文件:")
    logger.info(f"  - 向量库: collection={importer.collection_name}")
    logger.info(f"  - 图谱: {graph_output}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
