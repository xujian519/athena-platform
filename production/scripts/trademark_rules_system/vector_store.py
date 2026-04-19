#!/usr/bin/env python3
"""
商标规则向量存储（使用平台BGE-M3和Reranker）- 简化兼容版
Trademark Rules Vector Store - Simplified Compatible Version

基于Athena平台的优化模型：
1. BGE-M3向量化（MPS加速）
2. Qdrant向量存储
3. 可选的Reranker重排序

作者: Athena AI系统
创建时间: 2025-01-15
版本: 2.1.0
"""

from __future__ import annotations
import asyncio
import hashlib
import logging

# 平台服务导入
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Qdrant导入
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.embedding.bge_embedding_service import BGEEmbeddingService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrademarkVectorStore:
    """商标规则向量存储（BGE-M3集成）"""

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化向量存储"""
        self.config = config or {}

        # Qdrant配置
        self.qdrant_url = self.config.get('qdrant_url', 'http://localhost:6333')
        self.collection_name = self.config.get('collection_name', 'trademark_rules')

        # BGE-M3配置
        self.model_name = self.config.get('model_name', 'bge-m3')
        self.device = self.config.get('device', 'mps')

        # 批处理配置
        self.embedding_batch_size = self.config.get('embedding_batch_size', 32)
        self.upload_batch_size = self.config.get('upload_batch_size', 100)

        # 组件
        self.qdrant_client: QdrantClient | None = None
        self.embedding_service: BGEEmbeddingService | None = None

        # 统计
        self.stats = {
            'total_vectors': 0,
            'uploaded_vectors': 0,
            'failed_vectors': 0
        }

        logger.info("📦 商标规则向量存储初始化")
        logger.info(f"   模型: {self.model_name}, 设备: {self.device}")

    async def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            # 1. 连接Qdrant
            self.qdrant_client = QdrantClient(url=self.qdrant_url)

            # 创建集合
            try:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info("✅ Qdrant集合已创建")
            except Exception:
                logger.info("ℹ️  Qdrant集合已存在")

            # 2. 初始化BGE-M3
            logger.info(f"🔥 初始化BGE-M3（{self.device}）...")
            self.embedding_service = BGEEmbeddingService(
                model_name=self.model_name,
                device=self.device,
                batch_size=self.embedding_batch_size
            )
            logger.info("✅ BGE-M3已初始化")

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    def _generate_point_id(self, text: str, prefix: str = "tm") -> str:
        """生成点ID"""
        hash_value = hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()
        return f"{prefix}_{hash_value}"

    async def embed_text(self, text: str) -> list[float]:
        """文本向量化"""
        try:
            if self.embedding_service is None:
                raise RuntimeError("嵌入服务未初始化")

            embedding = self.embedding_service.encode([text])[0]
            return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)

        except Exception as e:
            logger.error(f"❌ 嵌入失败: {e}")
            return [0.0] * 1024

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        try:
            if self.embedding_service is None:
                raise RuntimeError("嵌入服务未初始化")

            embeddings = self.embedding_service.encode(texts)
            return [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]

        except Exception as e:
            logger.error(f"❌ 批量嵌入失败: {e}")
            return [[0.0] * 1024 for _ in texts]

    async def store_chunks(
        self,
        chunks: list[dict[str, Any]],
        norm_id: str
    ) -> int:
        """存储文本块向量"""
        if self.qdrant_client is None:
            logger.error("❌ Qdrant未初始化")
            return 0

        points = []
        uploaded_count = 0

        try:
            # 批量向量化
            texts = [chunk['text'] for chunk in chunks]
            logger.info(f"🔢 向量化 {len(texts)} 个文本块...")
            embeddings = await self.embed_batch(texts)

            # 创建向量点
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                point_id = self._generate_point_id(chunk['text'])

                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        'text': chunk['text'][:1000],
                        'norm_id': norm_id,
                        'chunk_id': chunk.get('chunk_id'),
                        'char_count': chunk.get('char_count', len(chunk['text'])),
                        'document_type': chunk.get('metadata', {}).get('document_type'),
                        'issuing_authority': chunk.get('metadata', {}).get('issuing_authority'),
                        'created_at': datetime.now().isoformat()
                    }
                )

                points.append(point)
                self.stats['total_vectors'] += 1

                # 批量上传
                if len(points) >= self.upload_batch_size:
                    uploaded = await self._upload_batch(points)
                    uploaded_count += uploaded
                    points = []

            # 上传剩余
            if points:
                uploaded = await self._upload_batch(points)
                uploaded_count += uploaded

            logger.info(f"✅ 存储完成: {uploaded_count} 个向量")
            return uploaded_count

        except Exception as e:
            logger.error(f"❌ 存储失败: {e}")
            return uploaded_count

    async def _upload_batch(self, points: list[PointStruct]) -> int:
        """批量上传"""
        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            self.stats['uploaded_vectors'] += len(points)
            return len(points)
        except Exception as e:
            logger.error(f"❌ 上传失败: {e}")
            return 0

    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """相似向量搜索"""
        if self.qdrant_client is None:
            return []

        try:
            # 向量化查询
            query_vector = await self.embed_text(query)

            # 搜索
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )

            # 格式化
            formatted = []
            for r in results:
                formatted.append({
                    'id': r.id,
                    'score': r.score,
                    'payload': r.payload
                })

            return formatted

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []

    async def get_collection_info(self) -> dict[str, Any]:
        """获取集合信息"""
        if self.qdrant_client is None:
            return {}

        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"❌ 获取信息失败: {e}")
            return {}

    async def close(self):
        """关闭资源"""
        logger.info("🔌 资源已释放")


async def main():
    """测试"""
    config = {
        'qdrant_url': 'http://localhost:6333',
        'collection_name': 'trademark_rules',
        'model_name': 'bge-m3',
        'device': 'mps'
    }

    store = TrademarkVectorStore(config)
    await store.initialize()

    # 测试搜索
    results = await store.search_similar("商标注册的条件", limit=5)
    print(f"结果: {len(results)} 条")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['score']:.4f}: {r['payload'].get('text', '')[:80]}...")

    await store.close()


if __name__ == "__main__":
    asyncio.run(main())
