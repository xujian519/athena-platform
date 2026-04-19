#!/usr/bin/env python3
"""
简化的BGE-M3和Reranker测试
Simple Test for BGE-M3 and Reranker
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import time

from core.embedding.bge_embedding_service import BGEEmbeddingService
from core.reranking.bge_reranker import BGEReranker, RerankConfig, RerankMode


async def test_embedding():
    """测试BGE-M3嵌入"""
    print("=" * 60)
    print("🔥 测试BGE-M3嵌入（MPS加速）")
    print("=" * 60)

    # 初始化
    print("\n📦 初始化BGE-M3...")
    embed_service = BGEEmbeddingService(
        model_name='bge-m3',
        device='mps',
        batch_size=32
    )

    # 测试文本
    texts = [
        "商标注册的条件包括具有显著性，便于识别。",
        "商标权的期限为10年，自核准注册之日起计算。",
        "两个或两个以上的商标注册申请人就同一种商品申请注册相同商标的，商标局初步审定并公告申请在先的商标。"
    ]

    print(f"\n📝 测试文本: {len(texts)} 条")

    # 向量化
    print("\n🔢 开始向量化...")
    start = time.time()
    embeddings = embed_service.encode(texts)
    elapsed = time.time() - start

    print("\n✅ 向量化完成!")
    print(f"   用时: {elapsed:.2f} 秒")
    print(f"   向量维度: {len(embeddings[0])}")
    print(f"   向量示例（前5维）: {embeddings[0][:5].tolist()}")

    return embeddings, embed_service


def test_reranker() -> Any:
    """测试Reranker（同步版本）"""
    print("\n" + "=" * 60)
    print("🔄 测试BGE-Reranker重排序")
    print("=" * 60)

    # 初始化
    print("\n📦 初始化Reranker...")
    reranker_config = RerankConfig(
        mode=RerankMode.TOP_K_RERANK,
        top_k=10,
        final_top_k=3
    )

    reranker = BGEReranker(
        model_path='/Users/xujian/Athena工作平台/models/converted/bge-reranker-large',
        config=reranker_config
    )

    reranker.initialize()
    print("✅ Reranker已初始化")

    # 测试数据 - BGEReranker需要字典格式，包含content字段
    query = "商标注册的条件是什么？"

    documents = [
        {"id": "1", "content": "商标注册申请人应当按规定的商品分类表填报使用商标的商品类别和商品名称。", "score": 0.7},
        {"id": "2", "content": "申请商标注册不得损害他人现有的在先权利，也不得以不正当手段抢先注册他人已经使用并有一定影响的商标。", "score": 0.75},
        {"id": "3", "content": "商标注册申请人应当对其使用商标的商品质量负责。", "score": 0.6},
        {"id": "4", "content": "商标权的期限为10年，自核准注册之日起计算。有效期届满需要继续使用的，应当在期满前12个月内办理续展手续。", "score": 0.5},
        {"id": "5", "content": "两个或者两个以上的商标注册申请人就同一种商品或者类似商品申请注册相同或者近似的商标的，商标局初步审定并公告申请在先的商标。", "score": 0.65}
    ]

    print(f"\n📝 查询: {query}")
    print(f"📚 文档数量: {len(documents)}")

    # 重排序
    print("\n🔄 开始重排序...")
    start = time.time()
    rerank_result = reranker.rerank(
        query=query,
        items=documents,
        config=reranker_config
    )
    elapsed = time.time() - start

    print(f"\n✅ 重排序完成! 用时: {elapsed:.2f} 秒")
    print("📊 结果:")

    # 显示原始排序
    print("\n原始排序:")
    for i, (item, score) in enumerate(zip(rerank_result.items, rerank_result.scores, strict=False), 1):
        content = item.get('content', '')
        print(f"   {i}. 分数: {score:.4f} | {content[:60]}...")

    # 显示重排序后结果
    print(f"\n重排序后 (Top-{len(rerank_result.reranked_items)}):")
    for i, (item, score) in enumerate(zip(rerank_result.reranked_items, rerank_result.reranked_scores, strict=False), 1):
        content = item.get('content', '')
        print(f"   {i}. 分数: {score:.4f} | {content[:60]}...")

    # 显示统计信息
    stats = reranker.get_stats()
    print("\n📊 统计信息:")
    print(f"   总重排序次数: {stats['total_reranks']}")
    print(f"   平均耗时: {stats['avg_time']:.3f}秒")
    print(f"   缓存命中率: {stats['cache_hit_rate']:.1%}")

    return True


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🧪 BGE-M3 + Reranker 简化测试")
    print("=" * 60)

    # 测试嵌入
    embeddings, embed_service = await test_embedding()

    # 测试重排序（同步调用）
    test_reranker()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
