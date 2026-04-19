#!/usr/bin/env python3
"""
法律数据向量化系统 (BGE-M3)
Legal Data Vectorization with BGE-M3

将PostgreSQL中的法律数据使用BGE-M3向量化并存储到Qdrant

作者: Athena AI系统
创建时间: 2025-01-15
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.embedding.bge_embedding_service import BGEEmbeddingService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LegalVectorizePipeline:
    """法律数据向量化管道（BGE-M3）"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # PostgreSQL配置
        self.pg_config = {
            'host': self.config.get('pg_host', 'localhost'),
            'port': self.config.get('pg_port', 5432),
            'database': self.config.get('pg_database', 'patent_legal_db'),
            'user': self.config.get('pg_user', 'xujian'),
            'password': self.config.get('pg_password', '')
        }

        # Qdrant配置
        self.qdrant_url = self.config.get('qdrant_url', 'http://localhost:6333')
        self.collection_name = self.config.get('collection_name', 'legal_articles_bge_m3')

        # BGE-M3配置
        self.model_name = self.config.get('model_name', 'bge-m3')
        self.device = self.config.get('device', 'mps')
        self.batch_size = self.config.get('batch_size', 32)

        # 组件
        self.pg_conn: psycopg2.extensions.connection | None = None
        self.qdrant_client: QdrantClient | None = None
        self.embedding_service: BGEEmbeddingService | None = None

        # 统计
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'total_vectors': 0,
            'start_time': datetime.now().isoformat()
        }

    async def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            # 1. 连接PostgreSQL
            logger.info(f"📦 连接PostgreSQL: {self.pg_config['database']}")
            self.pg_conn = psycopg2.connect(**self.pg_config)

            # 检查数据
            cur = self.pg_conn.cursor(cursor_factory=RealDictCursor)

            # 检查文档数量
            cur.execute("SELECT COUNT(*) as count FROM legal_documents")
            docs_count = cur.fetchone()['count']

            # 检查向量数量（如果有document_vectors表）
            try:
                cur.execute("SELECT COUNT(*) as count FROM document_vectors")
                vectors_count = cur.fetchone()['count']
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                vectors_count = 0

            cur.close()

            self.stats['total_documents'] = docs_count
            self.stats['total_chunks'] = vectors_count if vectors_count > 0 else docs_count

            logger.info(f"✅ PostgreSQL已连接: {docs_count} 文档, {vectors_count} 向量")

            # 2. 连接Qdrant
            logger.info(f"📦 连接Qdrant: {self.qdrant_url}")
            self.qdrant_client = QdrantClient(url=self.qdrant_url)

            # 确保集合存在
            try:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info(f"✅ Qdrant集合已创建: {self.collection_name}")
            except Exception:
                logger.info(f"ℹ️  Qdrant集合已存在: {self.collection_name}")

            # 3. 初始化BGE-M3
            logger.info(f"🔥 初始化BGE-M3（{self.device}）...")
            self.embedding_service = BGEEmbeddingService(
                model_name=self.model_name,
                device=self.device,
                batch_size=self.batch_size
            )
            logger.info("✅ BGE-M3已初始化")

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _fetch_documents_from_db(self, limit: int | None = None) -> list[dict[str, Any]]:
        """从数据库获取所有文档"""
        try:
            cur = self.pg_conn.cursor(cursor_factory=RealDictCursor)

            # 获取文档及其基本信息
            query = """
                SELECT
                    id,
                    file_name,
                    content,
                    document_type,
                    metadata
                FROM legal_documents
                WHERE content IS NOT NULL AND LENGTH(content) > 100
                ORDER BY created_at DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cur.execute(query)
            rows = cur.fetchall()
            cur.close()

            logger.info(f"📚 从数据库获取 {len(rows)} 个文档")
            return rows

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            return []

    def _fetch_document_vectors_from_db(self, limit: int | None = None) -> list[dict[str, Any]]:
        """从数据库获取所有文档向量（如果存在分块向量）"""
        try:
            cur = self.pg_conn.cursor(cursor_factory=RealDictCursor)

            # 检查document_vectors表是否存在
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'document_vectors'
                )
            """)
            exists = cur.fetchone()[0]

            if not exists:
                cur.close()
                return []

            # 获取分块向量
            query = """
                SELECT
                    id,
                    document_id,
                    chunk_index,
                    chunk_text,
                    metadata
                FROM document_vectors
                ORDER BY document_id, chunk_index
            """

            if limit:
                query += f" LIMIT {limit}"

            cur.execute(query)
            rows = cur.fetchall()
            cur.close()

            logger.info(f"📚 从数据库获取 {len(rows)} 个分块向量")
            return rows

        except Exception as e:
            logger.error(f"❌ 获取分块数据失败: {e}")
            return []

    async def vectorize_and_store_documents(self, documents: list[dict[str, Any]]) -> int:
        """向量化并存储完整文档到Qdrant"""
        if not documents:
            return 0

        try:
            logger.info(f"🔢 开始向量化 {len(documents)} 个文档...")

            # 批量向量化
            texts = [doc['content'] for doc in documents]
            embeddings = self.embedding_service.encode(texts)

            logger.info(f"✅ 向量化完成: {len(embeddings)} 个向量")

            # 创建向量点
            points = []
            for doc, embedding in zip(documents, embeddings, strict=False):
                # 生成整数ID (从UUID生成)
                doc_id_str = str(doc['id'])
                hash_value = int(hashlib.md5(doc_id_str.encode('utf-8'), usedforsecurity=False).hexdigest()[:8], 16)
                point_id = hash_value % (2**63)

                # 解析metadata
                metadata = doc.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        pass
                    except Exception as e:
                        logger.debug(f"空except块已触发: {e}")
                        metadata = {}

                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        'text': doc['content'][:2000],  # 限制文本长度
                        'document_id': doc_id_str,
                        'document_type': doc.get('document_type', 'unknown'),
                        'title': metadata.get('title', doc.get('file_name', '')),
                        'court': metadata.get('court', ''),
                        'date': metadata.get('date', ''),
                        'file_name': doc.get('file_name', ''),
                        'created_at': datetime.now().isoformat()
                    }
                )

                points.append(point)

            # 批量上传
            logger.info("📤 上传向量到Qdrant...")
            batch_size = 100
            uploaded = 0

            for i in tqdm(range(0, len(points), batch_size), desc="上传批次"):
                batch = points[i:i + batch_size]
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                uploaded += len(batch)

            logger.info(f"✅ 上传完成: {uploaded} 个向量")
            self.stats['total_vectors'] = uploaded

            return uploaded

        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0

    async def vectorize_and_store_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """向量化并存储分块到Qdrant"""
        if not chunks:
            return 0

        try:
            logger.info(f"🔢 开始向量化 {len(chunks)} 个分块...")

            # 批量向量化
            texts = [chunk['chunk_text'] for chunk in chunks]
            embeddings = self.embedding_service.encode(texts)

            logger.info(f"✅ 向量化完成: {len(embeddings)} 个向量")

            # 创建向量点
            points = []
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                # 生成整数ID
                hash_value = int(hashlib.md5(str(chunk['id'], usedforsecurity=False).encode()).hexdigest()[:8], 16)
                point_id = hash_value % (2**63)

                # 解析metadata
                metadata = chunk.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except Exception as e:
                        logger.debug(f"解析metadata失败: {e}")
                        metadata = {}

                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        'text': chunk['chunk_text'][:1000],
                        'document_id': chunk['document_id'],
                        'chunk_id': chunk['id'],
                        'chunk_index': chunk['chunk_index'],
                        'document_type': metadata.get('document_type', 'unknown'),
                        'title': metadata.get('title', ''),
                        'court': metadata.get('court', ''),
                        'created_at': datetime.now().isoformat()
                    }
                )

                points.append(point)

            # 批量上传
            logger.info("📤 上传向量到Qdrant...")
            batch_size = 100
            uploaded = 0

            for i in tqdm(range(0, len(points), batch_size), desc="上传批次"):
                batch = points[i:i + batch_size]
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                uploaded += len(batch)

            logger.info(f"✅ 上传完成: {uploaded} 个向量")
            self.stats['total_vectors'] = uploaded

            return uploaded

        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0

    async def run(self, use_chunks: bool = True, limit: int | None = None) -> dict[str, Any]:
        """运行管道"""
        try:
            logger.info("🚀 开始向量化管道")

            # 初始化
            if not await self.initialize():
                return {'status': 'error', 'message': '初始化失败'}

            # 获取数据
            if use_chunks:
                # 优先使用分块数据
                chunks = self._fetch_document_vectors_from_db(limit)
                if chunks:
                    count = await self.vectorize_and_store_chunks(chunks)
                else:
                    # 如果没有分块数据，使用完整文档
                    documents = self._fetch_documents_from_db(limit)
                    count = await self.vectorize_and_store_documents(documents)
            else:
                documents = self._fetch_documents_from_db(limit)
                count = await self.vectorize_and_store_documents(documents)

            # 获取集合信息
            collection_info = self.qdrant_client.get_collection(self.collection_name)

            self.stats['end_time'] = datetime.now().isoformat()
            self.stats['status'] = 'success'

            logger.info("✅ 向量化完成!")
            logger.info(f"📊 统计: {self.stats}")

            return {
                'status': 'success',
                'stats': self.stats,
                'collection_info': {
                    'points_count': collection_info.points_count,
                    'status': collection_info.status
                }
            }

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

            self.stats['status'] = 'error'
            self.stats['error'] = str(e)

            return {'status': 'error', 'stats': self.stats}

        finally:
            # 清理资源
            if self.pg_conn:
                self.pg_conn.close()
            logger.info("🔌 资源已释放")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='法律数据向量化（BGE-M3）')
    parser.add_argument('--limit', type=int, help='限制处理数量（测试用）')
    parser.add_argument('--full-documents', action='store_true', help='使用完整文档而非分块')
    args = parser.parse_args()

    config = {
        'pg_host': 'localhost',
        'pg_port': 5432,
        'pg_database': 'patent_legal_db',
        'pg_user': 'xujian',
        'pg_password': '',
        'qdrant_url': 'http://localhost:6333',
        'collection_name': 'legal_articles_bge_m3',
        'model_name': 'bge-m3',
        'device': 'mps',
        'batch_size': 32
    }

    pipeline = LegalVectorizePipeline(config)
    result = await pipeline.run(use_chunks=not args.full_documents, limit=args.limit)

    print("\n" + "=" * 60)
    print("📊 向量化完成")
    print("=" * 60)
    print(f"状态: {result['status']}")
    if result['status'] == 'success':
        print(f"向量总数: {result['stats']['total_vectors']}")
        print(f"集合状态: {result['collection_info']['status']}")
        print(f"集合点数: {result['collection_info']['points_count']}")
        print("\n💡 测试搜索:")
        print("   python3 production/scripts/legal_database_system/legal_search_engine.py")


if __name__ == "__main__":
    asyncio.run(main())
