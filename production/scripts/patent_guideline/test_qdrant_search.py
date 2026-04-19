#!/usr/bin/env python3
"""
专利审查指南语义搜索测试
测试Qdrant向量检索功能

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_semantic_search():
    """测试语义搜索功能"""

    print("=" * 60)
    print("🔍 专利审查指南语义搜索测试")
    print("=" * 60)

    # 1. 初始化BGE服务
    print("\n📦 加载BGE模型...")
    from core.nlp.bge_embedding_service import BGEEmbeddingService

    model_path = Path("/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5")
    if not model_path.exists():
        model_path = Path("/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5")

    config = {
        "model_path": str(model_path),
        "device": "cpu",
        "batch_size": 32,
        "max_length": 512,
        "normalize_embeddings": True,
        "cache_enabled": True,
        "preload": True
    }

    bge_service = BGEEmbeddingService(config)
    await bge_service.initialize()

    health = await bge_service.health_check()
    print(f"✅ BGE服务: {health['status']}, 维度: {health['dimension']}")

    # 2. 连接Qdrant
    print("\n🔗 连接Qdrant...")
    from qdrant_client import QdrantClient

    qdrant_client = QdrantClient(url="http://localhost:6333")

    collection_info = qdrant_client.get_collection("patent_guidelines")
    print("✅ 集合: patent_guidelines")
    print(f"   点数量: {collection_info.points_count}")
    print(f"   向量维度: {collection_info.config.params.vectors.size}")

    # 3. 测试查询
    test_queries = [
        "什么是专利的新颖性？",
        "发明专利的审查流程是什么？",
        "如何判断创造性？",
        "专利申请的优先权如何计算？",
        "专利无效宣告的理由有哪些？"
    ]

    print("\n" + "=" * 60)
    print("🔍 执行语义搜索测试")
    print("=" * 60)

    for query in test_queries:
        print(f"\n📝 查询: {query}")

        # 生成查询向量
        result = await bge_service.encode([query], task_type="patent_guideline")
        query_vector = result.embeddings[0]

        # 搜索 - 使用query_points替代search
        from qdrant_client.models import QueryVector

        search_results = qdrant_client.query_points(
            collection_name="patent_guidelines",
            query=QueryVector(vector=query_vector.tolist() if hasattr(query_vector, 'tolist') else list(query_vector)),
            limit=3,
            score_threshold=0.5
        )

        print(f"   找到 {len(search_results)} 个结果:")
        for i, hit in enumerate(search_results, 1):
            payload = hit.payload
            title = payload.get('title', 'N/A')
            part = payload.get('part', 'N/A')
            subsection = payload.get('subsection', 'N/A')
            score = hit.score

            print(f"   [{i}] 相似度: {score:.4f}")
            print(f"       位置: {part} > {subsection}")
            print(f"       标题: {title[:80]}...")

    print("\n" + "=" * 60)
    print("✅ 语义搜索测试完成")
    print("=" * 60)


async def test_laws_search():
    """测试法律法规搜索"""

    print("\n" + "=" * 60)
    print("📚 专利法律法规语义搜索测试")
    print("=" * 60)

    # 1. 初始化BGE服务
    print("\n📦 加载BGE模型...")
    from core.nlp.bge_embedding_service import BGEEmbeddingService

    model_path = Path("/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5")
    if not model_path.exists():
        model_path = Path("/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5")

    config = {
        "model_path": str(model_path),
        "device": "cpu",
        "batch_size": 32,
        "max_length": 512,
        "normalize_embeddings": True,
        "cache_enabled": True,
        "preload": True
    }

    bge_service = BGEEmbeddingService(config)
    await bge_service.initialize()

    # 2. 连接Qdrant
    print("\n🔗 连接Qdrant...")
    from qdrant_client import QdrantClient

    qdrant_client = QdrantClient(url="http://localhost:6333")

    collection_info = qdrant_client.get_collection("patent_laws")
    print("✅ 集合: patent_laws")
    print(f"   点数量: {collection_info.points_count}")

    # 3. 测试查询
    test_queries = [
        "专利权的保护期限是多久？",
        "什么是专利侵权？",
        "如何申请专利？"
    ]

    print("\n" + "=" * 60)
    print("🔍 执行语义搜索测试")
    print("=" * 60)

    for query in test_queries:
        print(f"\n📝 查询: {query}")

        # 生成查询向量
        result = await bge_service.encode([query], task_type="patent_laws")
        query_vector = result.embeddings[0]

        # 搜索 - 使用query_points替代search
        from qdrant_client.models import QueryVector

        search_results = qdrant_client.query_points(
            collection_name="patent_laws",
            query=QueryVector(vector=query_vector.tolist() if hasattr(query_vector, 'tolist') else list(query_vector)),
            limit=3,
            score_threshold=0.5
        )

        print(f"   找到 {len(search_results)} 个结果:")
        for i, hit in enumerate(search_results, 1):
            payload = hit.payload
            doc_type = payload.get('doc_type', 'N/A')
            title = payload.get('title', 'N/A')
            score = hit.score

            print(f"   [{i}] 相似度: {score:.4f}")
            print(f"       类型: {doc_type}")
            print(f"       标题: {title[:80]}...")

    print("\n" + "=" * 60)
    print("✅ 法律法规搜索测试完成")
    print("=" * 60)


async def main():
    """主函数"""
    # 测试审查指南搜索
    await test_semantic_search()

    # 测试法律法规搜索
    await test_laws_search()


if __name__ == "__main__":
    asyncio.run(main())
