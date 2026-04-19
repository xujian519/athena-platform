#!/usr/bin/env python3
"""
法律数据库搜索引擎 (BGE-M3 + Reranker)
Legal Database Search Engine with BGE-M3 and Reranker

统一使用平台优化的BGE-M3向量化模型和BGE-Reranker重排序模型

作者: Athena AI系统
创建时间: 2025-01-15
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import psycopg2
from qdrant_client import QdrantClient

from core.embedding.bge_embedding_service import BGEEmbeddingService
from core.reranking.bge_reranker import BGEReranker, RerankConfig, RerankMode

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LegalSearchEngine:
    """法律数据库搜索引擎（BGE-M3 + Reranker）"""

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

        # 组件
        self.pg_conn: psycopg2.extensions.connection | None = None
        self.embedding_service: BGEEmbeddingService | None = None
        self.reranker: BGEReranker | None = None
        self.qdrant_client: QdrantClient | None = None

    async def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            # 1. 连接PostgreSQL
            logger.info(f"📦 连接PostgreSQL: {self.pg_config['database']}")
            self.pg_conn = psycopg2.connect(**self.pg_config)

            # 2. 初始化BGE-M3
            logger.info(f"🔥 初始化BGE-M3（{self.device}）...")
            self.embedding_service = BGEEmbeddingService(
                model_name=self.model_name,
                device=self.device
            )
            logger.info("✅ BGE-M3已初始化")

            # 3. 初始化Reranker
            logger.info("🔄 初始化Reranker...")
            reranker_config = RerankConfig(
                mode=RerankMode.TOP_K_RERANK,
                top_k=50,          # 先获取Top-50
                final_top_k=10      # 重排序后返回Top-10
            )
            self.reranker = BGEReranker(
                model_path='/Users/xujian/Athena工作平台/models/converted/bge-reranker-large',
                config=reranker_config
            )
            self.reranker.initialize()
            logger.info("✅ Reranker已初始化")

            # 4. 连接Qdrant
            logger.info("📦 连接Qdrant...")
            self.qdrant_client = QdrantClient(url=self.qdrant_url)

            # 检查或创建集合
            try:
                from qdrant_client.models import Distance, VectorParams
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info(f"✅ Qdrant集合已创建: {self.collection_name}")
            except Exception:
                logger.info(f"ℹ️  Qdrant集合已存在: {self.collection_name}")

            # 获取集合信息
            info = self.qdrant_client.get_collection(self.collection_name)
            logger.info(f"✅ 集合状态: {info.status}, 点数量: {info.points_count}")

            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def search(
        self,
        query: str,
        top_k: int = 50,
        final_top_k: int = 10,
        use_reranker: bool = True,
        document_type: str | None = None
    ) -> dict[str, Any]:
        """
        执行法律搜索（向量搜索 + Reranker重排序）

        Args:
            query: 查询文本
            top_k: 向量搜索返回数量
            final_top_k: 最终返回数量
            use_reranker: 是否使用Reranker
            document_type: 文档类型过滤 (judgment, law, interpretation等)

        Returns:
            搜索结果
        """
        try:
            # 1. 向量化查询
            query_vector = self.embedding_service.encode([query])[0]

            # 2. 向量搜索
            logger.info(f"🔍 向量搜索: {query}")
            if document_type:
                # 使用过滤条件
                from qdrant_client.models import FieldCondition, Filter, MatchValue
                search_filter = Filter(
                    must=[FieldCondition(key="document_type", match=MatchValue(value=document_type))]
                )
            else:
                search_filter = None

            search_response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist(),
                limit=top_k,
                query_filter=search_filter
            )

            search_results = search_response.points
            logger.info(f"✅ 向量搜索完成: {len(search_results)} 个结果")

            # 3. 格式化结果
            items = []
            for result in search_results:
                items.append({
                    'id': str(result.id),
                    'score': result.score,
                    'content': result.payload.get('text', '')[:500],  # 限制长度
                    'document_id': result.payload.get('document_id'),
                    'document_type': result.payload.get('document_type'),
                    'title': result.payload.get('title', ''),
                    'court': result.payload.get('court', ''),
                    'date': result.payload.get('date', '')
                })

            # 4. 可选的Reranker重排序
            if use_reranker and len(items) > 0:
                logger.info("🔄 执行Reranker重排序...")
                rerank_result = self.reranker.rerank(
                    query=query,
                    items=items,
                    config=RerankConfig(
                        mode=RerankMode.TOP_K_RERANK,
                        top_k=top_k,
                        final_top_k=final_top_k
                    )
                )

                final_items = rerank_result.reranked_items
                final_scores = rerank_result.reranked_scores
                rerank_time = rerank_result.rerank_time
            else:
                final_items = items[:final_top_k]
                final_scores = [item['score'] for item in final_items]
                rerank_time = 0

            return {
                'query': query,
                'total_found': len(search_results),
                'returned': len(final_items),
                'results': list(zip(final_items, final_scores, strict=False)),
                'rerank_time': rerank_time
            }

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}

    async def close(self):
        """关闭资源"""
        if self.pg_conn:
            self.pg_conn.close()
        logger.info("🔌 资源已释放")


async def main():
    """主测试函数"""
    print("=" * 80)
    print("🧪 法律数据库搜索测试 (BGE-M3 + Reranker)")
    print("=" * 80)

    # 初始化搜索引擎
    config = {
        'pg_host': 'localhost',
        'pg_port': 5432,
        'pg_database': 'patent_legal_db',
        'pg_user': 'xujian',
        'pg_password': '',
        'qdrant_url': 'http://localhost:6333',
        'collection_name': 'legal_articles_bge_m3',
        'model_name': 'bge-m3',
        'device': 'mps'
    }

    engine = LegalSearchEngine(config)

    if not await engine.initialize():
        print("❌ 初始化失败")
        return

    # 检查是否有数据
    collection_info = engine.qdrant_client.get_collection(config['collection_name'])
    if collection_info.points_count == 0:
        print("\n⚠️  Qdrant集合为空，需要先运行向量化脚本")
        print("   运行: python3 production/scripts/legal_database_system/vectorize_legal_data.py")
    else:
        # 测试查询
        test_queries = [
            "专利侵权如何认定？",
            "商标注册的条件是什么？",
            "著作权保护期限是多久？",
            "什么是先用权抗辩？",
            "如何认定驰名商标？"
        ]

        for query in test_queries:
            print("\n" + "-" * 80)
            print(f"📝 查询: {query}")
            print("-" * 80)

            # 执行搜索（使用Reranker）
            result = await engine.search(
                query=query,
                top_k=50,
                final_top_k=5,
                use_reranker=True
            )

            if 'error' in result:
                print(f"❌ 错误: {result['error']}")
                continue

            print(f"\n找到 {result['total_found']} 个结果，返回 Top-{result['returned']}")
            if result['rerank_time'] > 0:
                print(f"重排序耗时: {result['rerank_time']:.3f}秒")

            for i, (item, score) in enumerate(result['results'], 1):
                print(f"\n{i}. 分数: {score:.4f}")
                print(f"   类型: {item.get('document_type', 'N/A')}")
                print(f"   标题: {item.get('title', 'N/A')[:80]}")
                print(f"   内容: {item.get('content', '')[:150]}...")

    # 清理资源
    await engine.close()

    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
