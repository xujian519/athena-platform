#!/usr/bin/env python3
"""
测试BGE-M3和Reranker的商标规则向量化
Test Trademark Rules Vectorization with BGE-M3 and Reranker

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.embedding.bge_embedding_service import BGEEmbeddingService
from core.reranking.bge_reranker import BGEReranker, RerankConfig, RerankMode


async def test_bge_m3():
    """测试BGE-M3向量化"""
    print("=" * 60)
    print("🔥 测试BGE-M3向量化（MPS加速）")
    print("=" * 60)

    # 初始化BGE-M3
    embedding_service = BGEEmbeddingService(
        model_name='bge-m3',
        device='mps',
        batch_size=32
    )

    # 测试文本
    test_texts = [
        "商标注册的条件包括具有显著性，便于识别，不得与他人在先权利冲突。",
        "商标申请人应当对其使用商标的商品质量负责。",
        "商标权的期限为10年，自核准注册之日起计算。"
    ]

    print(f"\n📝 测试文本: {len(test_texts)} 条")

    # 向量化
    print("\n🔢 开始向量化...")
    embeddings = embedding_service.encode(test_texts)

    print("✅ 向量化完成!")
    print(f"   向量维度: {len(embeddings[0])}")
    print(f"   向量示例（前10维）: {embeddings[0][:10].tolist()}")

    return embeddings


async def test_qdrant_store():
    """测试Qdrant存储"""
    print("\n" + "=" * 60)
    print("💾 测试Qdrant向量存储")
    print("=" * 60)

    # 连接Qdrant
    qdrant = QdrantClient(url="http://localhost:6333")

    # 创建集合
    collection_name = "trademark_rules_test"
    try:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
        print(f"✅ 集合已创建: {collection_name}")
    except Exception:
        print(f"ℹ️  集合已存在: {collection_name}")

    # 初始化BGE-M3
    embedding_service = BGEEmbeddingService(
        model_name='bge-m3',
        device='mps'
    )

    # 测试数据
    test_docs = [
        "商标注册申请人应当按规定的商品分类表填报使用商标的商品类别和商品名称。",
        "商标注册申请人在不同类别的商品上申请注册同一商标的，应当按类分别提出注册申请。",
        "注册商标需要在核定使用范围之外的商品上取得商标专用权的，应当另行提出注册申请。"
    ]

    # 向量化并存储
    print(f"\n📦 存储 {len(test_docs)} 个文档...")
    for i, doc in enumerate(test_docs):
        # 向量化
        embedding = embedding_service.encode([doc])[0]

        # 生成整数ID（使用哈希的前8位十六进制转整数）
        hash_value = int(hashlib.md5(doc.encode('utf-8'), usedforsecurity=False).hexdigest()[:8], 16)
        doc_id = hash_value % (2**63)  # 确保在有效范围内

        # 创建点
        point = PointStruct(
            id=doc_id,
            vector=embedding.tolist(),
            payload={
                'text': doc,
                'index': i
            }
        )

        # 上传
        qdrant.upsert(
            collection_name=collection_name,
            points=[point]
        )
        print(f"   ✅ 文档 {i+1} 已存储")

    # 测试搜索
    print("\n🔍 测试向量搜索...")
    query = "如何申请商标注册"
    query_vector = embedding_service.encode([query])[0].tolist()

    results = qdrant.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=3
    )

    print(f"✅ 找到 {len(results)} 个结果:")
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. 相似度: {result.score:.4f}")
        print(f"      文本: {result.payload['text'][:80]}...")

    # 获取集合信息
    info = qdrant.get_collection(collection_name)
    print("\n📊 集合统计:")
    print(f"   点数量: {info.points_count}")
    print(f"   状态: {info.status}")

    return True


async def test_reranker():
    """测试BGE-Reranker重排序"""
    print("\n" + "=" * 60)
    print("🔄 测试BGE-Reranker重排序")
    print("=" * 60)

    # 初始化Reranker
    reranker_config = RerankConfig(
        mode=RerankMode.TOP_K_RERANK,
        top_k=10,
        final_top_k=3,
        threshold=0.2,
        batch_size=16
    )

    reranker = BGEReranker(
        model_path='/Users/xujian/Athena工作平台/models/converted/bge-reranker-large',
        config=reranker_config
    )

    print("🔄 初始化Reranker...")
    await reranker.initialize_async()
    print("✅ Reranker已初始化")

    # 测试数据
    query = "商标注册的条件和流程"

    documents = [
        "商标注册申请人应当按规定的商品分类表填报使用商标的商品类别和商品名称。",
        "申请商标注册不得损害他人现有的在先权利，也不得以不正当手段抢先注册他人已经使用并有一定影响的商标。",
        "商标注册申请人应当对其使用商标的商品质量负责。各级工商行政管理部门应当通过商标管理，制止欺骗消费者的行为。",
        "商标权的期限为10年，自核准注册之日起计算。有效期届满需要继续使用的，应当在期满前12个月内办理续展手续。",
        "两个或者两个以上的商标注册申请人就同一种商品或者类似商品申请注册相同或者近似的商标的，商标局初步审定并公告申请在先的商标。"
    ]

    print(f"\n📝 查询: {query}")
    print(f"📚 文档数量: {len(documents)}")

    # 重排序
    print("\n🔄 开始重排序...")
    rerank_result = await reranker.rerank_async(
        query=query,
        documents=documents,
        top_k=3
    )

    print("\n✅ 重排序完成!")
    print("📊 结果:")
    for i, result in enumerate(rerank_result.results, 1):
        print(f"\n   {i}. 分数: {result.score:.4f}")
        print(f"      索引: {result.index}")
        doc_text = documents[result.index]
        print(f"      文本: {doc_text[:80]}...")

    await reranker.close_async()

    return True


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 BGE-M3 + Reranker 集成测试")
    print("=" * 60)

    # 测试1: BGE-M3向量化
    embeddings = await test_bge_m3()

    # 测试2: Qdrant存储
    await test_qdrant_store()

    # 测试3: Reranker重排序
    await test_reranker()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
