#!/usr/bin/env python3
import asyncio
import logging
import sys
sys.path.insert(0, 'patent_hybrid_retrieval')

# 设置详细日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

from real_patent_hybrid_retrieval import RealPatentHybridRetrieval

async def test_retrieval():
    try:
        retriever = RealPatentHybridRetrieval()
        print("\n=== 开始检索 ===")
        results = await retriever.search("人工智能", top_k=5)

        print(f"\n找到 {len(results)} 条结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result.patent_id}] {result.title}")
            print(f"   分数: {result.score:.4f}")
            print(f"   来源: {result.source}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_retrieval())
