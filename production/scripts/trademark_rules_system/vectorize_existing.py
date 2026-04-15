#!/usr/bin/env python3
"""
将PostgreSQL中现有的商标规则数据向量化并存储到Qdrant
Vectorize existing trademark rules from PostgreSQL to Qdrant

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.embedding.bge_embedding_service import BGEEmbeddingService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrademarkVectorizePipeline:
    """向量化现有数据管道"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # PostgreSQL配置
        self.pg_config = {
            'host': self.config.get('pg_host', 'localhost'),
            'port': self.config.get('pg_port', 5432),
            'database': self.config.get('pg_database', 'trademark_database'),
            'user': self.config.get('pg_user', os.getenv('USER', 'xujian')),
            'password': self.config.get('pg_password', '')
        }

        # Qdrant配置
        self.qdrant_url = self.config.get('qdrant_url', 'http://localhost:6333')
        self.collection_name = self.config.get('collection_name', 'trademark_rules')

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
            'total_norms': 0,
            'total_articles': 0,
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
            cur = self.pg_conn.cursor()
            cur.execute("SELECT COUNT(*) FROM trademark_norms")
            norms_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM trademark_articles")
            articles_count = cur.fetchone()[0]
            cur.close()

            self.stats['total_norms'] = norms_count
            self.stats['total_articles'] = articles_count

            logger.info(f"✅ PostgreSQL已连接: {norms_count} 法规, {articles_count} 条款")

            # 2. 连接Qdrant
            logger.info(f"📦 连接Qdrant: {self.qdrant_url}")
            self.qdrant_client = QdrantClient(url=self.qdrant_url)

            # 确保集合存在
            try:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info("✅ Qdrant集合已创建")
            except Exception:
                logger.info("ℹ️  Qdrant集合已存在")

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

    def _fetch_articles_from_db(self) -> list[dict[str, Any]]:
        """从数据库获取所有条款"""
        try:
            cur = self.pg_conn.cursor()

            # 获取条款及其所属法规信息
            query = """
                SELECT
                    a.id,
                    a.norm_id,
                    a.article_number,
                    a.original_text,
                    a.hierarchy_path,
                    n.name as norm_name,
                    n.issuing_authority,
                    n.document_type
                FROM trademark_articles a
                JOIN trademark_norms n ON a.norm_id = n.id
                ORDER BY n.id, a.article_number
            """

            cur.execute(query)
            rows = cur.fetchall()
            cur.close()

            articles = []
            for row in rows:
                articles.append({
                    'id': row[0],
                    'norm_id': row[1],
                    'article_number': row[2],
                    'text': row[3],
                    'hierarchy_path': row[4],
                    'norm_name': row[5],
                    'issuing_authority': row[6],
                    'document_type': row[7]
                })

            logger.info(f"📚 从数据库获取 {len(articles)} 个条款")
            return articles

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            return []

    async def vectorize_and_store(self, articles: list[dict[str, Any]]) -> int:
        """向量化并存储到Qdrant"""
        if not articles:
            return 0

        try:
            logger.info(f"🔢 开始向量化 {len(articles)} 个条款...")

            # 批量向量化
            texts = [article['text'] for article in articles]
            embeddings = self.embedding_service.encode(texts)

            logger.info(f"✅ 向量化完成: {len(embeddings)} 个向量")

            # 创建向量点
            points = []
            for article, embedding in zip(articles, embeddings, strict=False):
                # 生成整数ID
                hash_value = int(hashlib.md5(article['id'].encode('utf-8'), usedforsecurity=False).hexdigest()[:8], 16)
                point_id = hash_value % (2**63)

                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        'text': article['text'][:1000],  # 限制文本长度
                        'article_id': article['id'],
                        'norm_id': article['norm_id'],
                        'article_number': article['article_number'],
                        'norm_name': article['norm_name'],
                        'issuing_authority': article['issuing_authority'],
                        'document_type': article['document_type'],
                        'hierarchy_path': article['hierarchy_path'],
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

    async def run(self) -> dict[str, Any]:
        """运行管道"""
        try:
            logger.info("🚀 开始向量化管道")

            # 初始化
            if not await self.initialize():
                return {'status': 'error', 'message': '初始化失败'}

            # 获取数据
            articles = self._fetch_articles_from_db()
            if not articles:
                return {'status': 'error', 'message': '没有数据'}

            # 向量化并存储
            count = await self.vectorize_and_store(articles)

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
    config = {
        'pg_host': 'localhost',
        'pg_port': 5432,
        'pg_database': 'trademark_database',
        'pg_user': 'xujian',
        'pg_password': '',
        'qdrant_url': 'http://localhost:6333',
        'collection_name': 'trademark_rules',
        'model_name': 'bge-m3',
        'device': 'mps',
        'batch_size': 32
    }

    pipeline = TrademarkVectorizePipeline(config)
    result = await pipeline.run()

    print("\n" + "=" * 60)
    print("📊 向量化完成")
    print("=" * 60)
    print(f"状态: {result['status']}")
    if result['status'] == 'success':
        print(f"向量总数: {result['stats']['total_vectors']}")
        print(f"集合状态: {result['collection_info']['status']}")
        print(f"集合点数: {result['collection_info']['points_count']}")


if __name__ == "__main__":
    asyncio.run(main())
