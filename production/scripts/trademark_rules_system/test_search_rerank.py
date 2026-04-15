#!/usr/bin/env python3
"""
测试商标规则向量搜索和Reranker
Test Trademark Rules Vector Search with Reranker

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from qdrant_client import QdrantClient

from core.embedding.bge_embedding_service import BGEEmbeddingService
from core.reranking.bge_reranker import BGEReranker, RerankConfig, RerankMode

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TrademarkSearchEngine:
    """商标规则搜索引擎（向量搜索 + Reranker）"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 配置
        self.qdrant_url = self.config.get('qdrant_url', 'http://localhost:6333')
        self.collection_name = self.config.get('collection_name', 'trademark_rules')
        self.model_name = self.config.get('model_name', 'bge-m3')
        self.device = self.config.get('device', 'mps')

        # 组件
        self.embedding_service: BGEEmbeddingService | None = None
        self.reranker: BGEReranker | None = None
        self.qdrant_client: QdrantClient | None = None

    async def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            # 1. 初始化嵌入服务
            logger.info(f"🔥 初始化BGE-M3（{self.device}）...")
            self.embedding_service = BGEEmbeddingService(
                model_name=self.model_name,
                device=self.device
            )

            # 2. 初始化Reranker
            logger.info("🔄 初始化Reranker...")
            reranker_config = RerankConfig(
                mode=RerankMode.TOP_K_RERANK,
                top_k=20,          # 先获取Top-20
                final_top_k=5      # 重排序后返回Top-5
            )
            self.reranker = BGEReranker(
                model_path='/Users/xujian/Athena工作平台/models/converted/bge-reranker-large',
                config=reranker_config
            )
            self.reranker.initialize()

            # 3. 连接Qdrant
            logger.info("📦 连接Qdrant...")
            self.qdrant_client = QdrantClient(url=self.qdrant_url)

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
        top_k: int = 20,
        final_top_k: int = 5,
        use_reranker: bool = True
    ) -> dict[str, Any]:
        """
        执行搜索（可选Reranker重排序）

        Args:
            query: 查询文本
            top_k: 向量搜索返回数量
            final_top_k: 最终返回数量
            use_reranker: 是否使用Reranker

        Returns:
            搜索结果
        """
        try:
            # 1. 向量化查询
            query_vector = self.embedding_service.encode([query])[0]

            # 2. 向量搜索
            logger.info(f"🔍 向量搜索: {query}")
            search_response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist(),
                limit=top_k
            )

            search_results = search_response.points
            logger.info(f"✅ 向量搜索完成: {len(search_results)} 个结果")

            # 3. 格式化结果
            items = []
            for result in search_results:
                items.append({
                    'id': str(result.id),
                    'score': result.score,
                    'content': result.payload.get('text', ''),
                    'article_number': result.payload.get('article_number'),
                    'norm_name': result.payload.get('norm_name'),
                    'issuing_authority': result.payload.get('issuing_authority')
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
        logger.info("🔌 资源已释放")


async def main():
    """主测试函数"""
    print("=" * 70)
    print("🧪 商标规则向量搜索 + Reranker 测试")
    print("=" * 70)

    # 初始化搜索引擎
    config = {
        'qdrant_url': 'http://localhost:6333',
        'collection_name': 'trademark_rules',
        'model_name': 'bge-m3',
        'device': 'mps'
    }

    engine = TrademarkSearchEngine(config)

    if not await engine.initialize():
        print("❌ 初始化失败")
        return

    # 测试查询
    test_queries = [
        "商标注册的条件是什么？",
        "商标权的保护期限是多久？",
        "如何申请商标续展？",
        "商标侵权如何认定？",
        "什么情况下商标会被驳回？"
    ]

    for query in test_queries:
        print("\n" + "-" * 70)
        print(f"📝 查询: {query}")
        print("-" * 70)

        # 执行搜索（使用Reranker）
        result = await engine.search(
            query=query,
            top_k=20,
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
            print(f"   条号: {item.get('article_number', 'N/A')}")
            print(f"   法规: {item.get('norm_name', 'N/A')}")
            print(f"   内容: {item.get('content', '')[:100]}...")

    # 清理资源
    await engine.close()

    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
