#!/usr/bin/env python3
"""
BGE集成测试脚本
Test BGE Integration for Athena Platform
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

async def test_bge_service():
    """测试BGE嵌入服务"""
    print("🚀 测试BGE嵌入服务...")
    print("=" * 50)

    try:
        from core.ai.nlp.bge_embedding_service import get_bge_service

        # 初始化服务
        bge_service = await get_bge_service()
        print("✅ BGE服务初始化成功")

        # 获取模型信息
        model_info = bge_service.get_model_info()
        print("\n📊 模型信息:")
        print(f"   - 名称: {model_info['name']}")
        print(f"   - 维度: {model_info['dimension']}")
        print(f"   - 设备: {model_info['device']}")
        print(f"   - 缓存: {'启用' if model_info['cache_enabled'] else '禁用'}")

        # 测试编码
        test_text = "本发明涉及一种新型的专利检索方法，利用深度学习技术提高检索精度。"
        result = await bge_service.encode(test_text, task_type="patent_search")

        print("\n📝 测试编码结果:")
        print(f"   - 处理时间: {result.processing_time:.3f}秒")
        print(f"   - 向量维度: {result.dimension}")
        print(f"   - 向量前5位: {[f'{x:.4f}' for x in result.embeddings[:5]}")

        # 批量测试
        test_texts = [
            "专利权利要求书的撰写规范",
            "技术交底书的准备要点",
            "发明专利申请流程",
            "实用新型专利审查指南"
        ]

        batch_result = await bge_service.encode(test_texts, task_type="patent_analysis")
        print("\n📚 批量编码测试:")
        print(f"   - 文本数量: {batch_result.batch_size}")
        print(f"   - 处理时间: {batch_result.processing_time:.3f}秒")
        print(f"   - 平均每文本: {batch_result.processing_time/batch_result.batch_size:.3f}秒")

        # 缓存测试
        print("\n💾 缓存测试...")
        start_time = time.time()
        await bge_service.encode(test_text, task_type="patent_search")
        cache_time = time.time() - start_time
        print(f"   - 缓存命中时间: {cache_time:.6f}秒")
        print(f"   - 性能提升: {result.processing_time/cache_time:.0f}倍")

        # 健康检查
        health = await bge_service.health_check()
        print("\n🏥 健康检查:")
        print(f"   - 状态: {health['status']}")
        print(f"   - 模型加载: {health['model_loaded']}")
        print(f"   - 测试编码: {health.get('test_encoding', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ BGE服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_model_router():
    """测试模型路由器BGE集成"""
    print("\n🎯 测试模型路由器BGE集成...")
    print("=" * 50)

    try:
        from core.orchestration.xiaonuo_model_router import XiaonuoModelRouter

        router = XiaonuoModelRouter()
        print("✅ 模型路由器加载成功")

        # 测试不同任务类型的嵌入
        tasks = [
            ("专利检索测试文本", "patent_search"),
            ("法律条款分析", "legal_analysis"),
            ("快速对话测试", "simple_chat")
        ]

        for text, task_type in tasks:
            print(f"\n📝 任务类型: {task_type}")
            start_time = time.time()
            embedding = await router.get_embedding(text, task_type)
            elapsed = time.time() - start_time

            if embedding:
                print("   ✅ 成功获取嵌入向量")
                print(f"   - 维度: {len(embedding)}")
                print(f"   - 用时: {elapsed:.3f}秒")

                # 分析使用的模型
                if len(embedding) == 1024:
                    print("   - 使用模型: BGE Large ZH v1.5")
                else:
                    print("   - 使用模型: Ollama nomic-embed-text")
            else:
                print("   ❌ 获取嵌入失败")

        return True

    except Exception as e:
        print(f"❌ 模型路由器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_patent_search():
    """测试BGE专利搜索"""
    print("\n🔍 测试BGE专利搜索...")
    print("=" * 50)

    try:
        from core.search.bge_patent_search import BGEPatentSearch

        searcher = BGEPatentSearch()
        await searcher.initialize()
        print("✅ BGE专利搜索初始化成功")

        # 测试专利搜索
        query = "基于深度学习的图像识别技术"
        results = await searcher.search_patents(query, top_k=5)

        print(f"\n📋 搜索结果 (查询: {query}):")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   - 专利号: {result.patent_id}")
            print(f"   - 相似度: {result.similarity:.3f}")
            print(f"   - 摘要: {result.abstract[:100]}...")

        # 获取搜索统计
        stats = searcher.get_statistics()
        print(f"\n📊 搜索统计: {stats}")

        return True

    except Exception as e:
        print(f"❌ 专利搜索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_redis_cache():
    """测试Redis缓存"""
    print("\n💾 测试Redis缓存...")
    print("=" * 50)

    try:
        from core.cache.bge_redis_cache import get_bge_redis_cache

        # 初始化缓存
        cache = await get_bge_redis_cache()
        print("✅ Redis缓存初始化成功")

        # 获取缓存统计
        stats = cache.get_stats()
        print("\n📊 缓存统计:")
        print(f"   - 连接状态: {'已连接' if stats['connected'] else '未连接'}")
        print(f"   - 缓存前缀: {stats['prefix']}")
        print(f"   - TTL: {stats['ttl']}秒")
        if 'cached_embeddings' in stats:
            print(f"   - 缓存向量数: {stats['cached_embeddings']}")

        # 健康检查
        health = await cache.health_check()
        print("\n🏥 健康检查:")
        print(f"   - 状态: {health['status']}")
        print(f"   - Redis测试: {health.get('redis_test', 'N/A')}")
        if 'memory_test' in health:
            print(f"   - 内存测试: {health['memory_test']}")

        return True

    except Exception as e:
        print(f"⚠️ Redis缓存测试失败（可能是Redis未运行）: {e}")
        return False

async def performance_benchmark():
    """性能基准测试"""
    print("\n🏃 性能基准测试...")
    print("-" * 30)

    from core.orchestration.xiaonuo_model_router import XiaonuoModelRouter

    from core.ai.nlp.bge_embedding_service import get_bge_service

    # 获取服务
    bge_service = await get_bge_service()
    router = XiaonuoModelRouter()

    # 测试文本
    test_cases = [
        ("本发明提供了一种新型的电池管理系统，包括电池状态监测模块、电量计算模块和安全保护模块。", "patent_analysis"),
        ("权利要求书是确定专利保护范围的重要法律文件。", "legal_analysis"),
        ("你好，我想了解专利申请的基本流程。", "simple_chat"),
        ("机器学习在自然语言处理中的应用有哪些？", "technical_reasoning")
    ] * 10

    print(f"\n总共 {len(test_cases)} 个测试用例...")

    # BGE测试
    print("\n🔹 BGE性能测试:")
    start_time = time.time()
    for text, task_type in test_cases:
        await bge_service.encode(text, task_type)
    bge_time = time.time() - start_time
    bge_avg = bge_time / len(test_cases)
    print(f"   - 总时间: {bge_time:.2f}秒")
    print(f"   - 平均每文本: {bge_avg:.3f}秒")
    print(f"   - 吞吐量: {len(test_cases)/bge_time:.1f} 文本/秒")

    # 模型路由器测试
    print("\n🔹 模型路由器测试:")
    start_time = time.time()
    for text, task_type in test_cases:
        await router.get_embedding(text, task_type)
    router_time = time.time() - start_time
    router_avg = router_time / len(test_cases)
    print(f"   - 总时间: {router_time:.2f}秒")
    print(f"   - 平均每文本: {router_avg:.3f}秒")
    print(f"   - 吞吐量: {len(test_cases)/router_time:.1f} 文本/秒")

    # 性能对比
    if router_time > 0:
        print("\n📈 性能对比:")
        print(f"   - BGE直接调用: {bge_time:.2f}秒")
        print(f"   - 路由器调用: {router_time:.2f}秒")
        print(f"   - 路由开销: {((router_time - bge_time) / bge_time * 100):.1f}%")

async def main():
    """主函数"""
    print("🧪 BGE Large ZH v1.5 集成测试")
    print("=" * 60)

    all_passed = True

    # 1. 测试BGE服务
    if not await test_bge_service():
        all_passed = False

    # 2. 测试模型路由器
    if not await test_model_router():
        all_passed = False

    # 3. 测试专利搜索
    if not await test_patent_search():
        all_passed = False

    # 4. 测试Redis缓存
    await test_redis_cache()  # 不影响整体结果

    # 5. 性能基准测试
    await performance_benchmark()

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎊 所有测试通过！")
        print("✅ BGE Large ZH v1.5 成功集成到平台")
        print("✅ 模型路由器智能选择已启用")
        print("✅ 专利检索功能已增强")
        print("✨ 平台NLP能力大幅提升！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")

if __name__ == "__main__":
    asyncio.run(main())
