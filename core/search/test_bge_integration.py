#!/usr/bin/env python3
from __future__ import annotations
"""
测试BGE模型集成到智能路由系统

测试真实BGE向量在Qdrant中的搜索效果
"""

import os
import sys
from typing import Any

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_bge_integration() -> Any:
    """测试BGE模型集成"""

    print("\n" + "=" * 70)
    print("🧪 测试BGE模型集成到智能路由系统")
    print("=" * 70)

    # 测试查询
    test_queries = ["智能农业设备的专利申请", "专利法第22条关于新颖性的规定", "专利侵权如何认定"]

    try:
        from core.search.intelligent_router import get_router

        router = get_router()

        for query in test_queries:
            print(f"\n🔍 查询: {query}")
            print("-" * 70)

            start_time = time.time()
            result = router.route_and_search(query, limit=5)
            total_time = time.time() - start_time

            print(f"✅ 意图: {result.query_context.intent.value}")
            print(f"✅ 置信度: {result.query_context.confidence:.2f}")
            print(f"✅ 数据源: {[ds.value for ds in result.query_context.data_sources]}")
            print(
                f"✅ 总耗时: {result.total_time:.3f}秒 (BGE编码: {total_time - result.total_time:.3f}秒)"
            )
            print(f"✅ 结果数: {len(result.results)}")

            print("\n📊 结果来源统计:")
            for source, stats in result.source_stats.items():
                count = stats.get("count", 0)
                print(f"  {source}: {count}条")

            if result.results:
                print("\n📝 Top 3 结果:")
                for i, r in enumerate(result.results[:3], 1):
                    content_preview = r.content[:80].replace("\n", " ")
                    print(f"  {i}. [{r.source.value}] {content_preview}... (score: {r.score:.4f})")
            else:
                print("\n⚠️ 未找到相关结果")

        router.close()

        print("\n" + "=" * 70)
        print("🎉 BGE模型集成测试完成!")
        print("=" * 70)

        print("\n💡 观察要点:")
        print("  1. 向量维度应该是1024维(bge-large)")
        print("  2. 搜索结果应该与查询语义相关")
        print("  3. 分数应该更有意义(不再随机)")
        print("  4. 首次查询会加载模型,后续查询更快")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_bge_integration()
    sys.exit(0 if success else 1)
