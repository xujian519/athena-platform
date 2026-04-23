#!/usr/bin/env python3
"""
验证text_embedding工具修复（方案1实施）
测试BGE嵌入服务集成
"""
import asyncio
import sys
import time

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


async def test_bge_service():
    """测试BGE服务"""
    print("\n" + "=" * 60)
    print("测试1: BGE嵌入服务")
    print("=" * 60)

    try:
        from core.nlp.bge_embedding_service import get_bge_service

        print("⏳ 获取BGE服务实例...")
        bge_service = await get_bge_service()

        print("✅ BGE服务初始化成功")
        print(f"   - 模型信息: {bge_service.get_model_info()}")

        # 测试编码
        print("\n⏳ 测试文本编码...")
        test_text = "这是一个测试文本，用于验证BGE嵌入服务。"
        result = await bge_service.encode(test_text)

        print("✅ 文本编码成功")
        print(f"   - 模型: {result.model_name}")
        print(f"   - 向量维度: {result.dimension}")
        print(f"   - 处理时间: {result.processing_time:.3f}秒")
        print(f"   - 缓存命中: {result.metadata.get('cache_hit', False)}")
        print(f"   - 向量前5维: {result.embeddings[:5] if isinstance(result.embeddings, list) else list(result.embeddings)[:5]}")

        return True

    except Exception as e:
        print(f"❌ BGE服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_text_embedding_handler():
    """测试text_embedding_handler"""
    print("\n" + "=" * 60)
    print("测试2: text_embedding_handler")
    print("=" * 60)

    try:
        from core.tools.production_tool_implementations import text_embedding_handler

        test_cases = [
            {
                "name": "中文短文本",
                "text": "专利检索是专利分析的基础",
                "expected_dim": 1024
            },
            {
                "name": "英文短文本",
                "text": "This is a test text for embedding",
                "expected_dim": 1024
            },
            {
                "name": "空文本",
                "text": "",
                "expected_dim": 1024
            },
            {
                "name": "长文本",
                "text": "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，"
                       "它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。"
                       "该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。",
                "expected_dim": 1024
            }
        ]

        success_count = 0

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {test_case['name']}")
            print(f"   文本: {test_case['text'][:50]}...")

            start_time = time.time()

            result = await text_embedding_handler(
                params={
                    "text": test_case['text'],
                    "model": "bge-large-zh-v1.5",
                    "normalize": True
                },
                context={}
            )

            elapsed_time = time.time() - start_time

            print(f"   响应时间: {elapsed_time:.3f}秒")
            print(f"   成功: {result.get('success', False)}")
            print(f"   模型: {result.get('model', 'N/A')}")
            print(f"   向量维度: {result.get('embedding_dim', 0)}")
            print(f"   消息: {result.get('message', 'N/A')}")

            if result.get('success'):
                print(f"   向量前5维: {result.get('embedding', [])[:5]}")
                print(f"   缓存命中: {result.get('cache_hit', False)}")
                print(f"   处理时间: {result.get('processing_time', 0):.3f}秒")

                # 验证维度
                if result.get('embedding_dim') == test_case['expected_dim']:
                    print(f"   ✅ 维度正确")
                    success_count += 1
                else:
                    print(f"   ❌ 维度错误，期望{test_case['expected_dim']}，实际{result.get('embedding_dim', 0)}")
            else:
                print(f"   ❌ 失败: {result.get('error', 'Unknown error')}")

        print(f"\n测试通过率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")

        return success_count == len(test_cases)

    except Exception as e:
        print(f"❌ text_embedding_handler测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_embedding():
    """测试批量嵌入"""
    print("\n" + "=" * 60)
    print("测试3: 批量文本嵌入")
    print("=" * 60)

    try:
        from core.nlp.bge_embedding_service import get_bge_service

        bge_service = await get_bge_service()

        texts = [
            "专利检索是专利分析的基础",
            "人工智能是计算机科学的一个分支",
            "机器学习是人工智能的核心技术",
            "深度学习是机器学习的一个子集",
            "自然语言处理是AI的重要应用"
        ]

        print(f"⏳ 批量编码 {len(texts)} 个文本...")
        start_time = time.time()

        result = await bge_service.encode(texts)

        elapsed_time = time.time() - start_time

        print("✅ 批量编码成功")
        print(f"   - 文本数量: {result.batch_size}")
        print(f"   - 向量维度: {result.dimension}")
        print(f"   - 总时间: {elapsed_time:.3f}秒")
        print(f"   - 平均时间: {elapsed_time/result.batch_size:.3f}秒/个")
        print(f"   - 吞吐量: {result.batch_size/elapsed_time:.1f} 文本/秒")

        return True

    except Exception as e:
        print(f"❌ 批量嵌入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "=" * 60)
    print("测试4: 缓存性能测试")
    print("=" * 60)

    try:
        from core.nlp.bge_embedding_service import get_bge_service

        bge_service = await get_bge_service()

        test_text = "缓存性能测试文本"

        # 第一次调用（无缓存）
        print("⏳ 第一次调用（无缓存）...")
        start_time = time.time()
        result1 = await bge_service.encode(test_text)
        time1 = time.time() - start_time

        print(f"   - 处理时间: {time1:.3f}秒")
        print(f"   - 缓存命中: {result1.metadata.get('cache_hit', False)}")

        # 第二次调用（有缓存）
        print("\n⏳ 第二次调用（有缓存）...")
        start_time = time.time()
        result2 = await bge_service.encode(test_text)
        time2 = time.time() - start_time

        print(f"   - 处理时间: {time2:.3f}秒")
        print(f"   - 缓存命中: {result2.metadata.get('cache_hit', False)}")
        print(f"   - 性能提升: {(time1-time2)/time1*100:.1f}%")

        # 查看统计信息
        stats = bge_service.get_statistics()
        print("\n📊 统计信息:")
        print(f"   - 总请求数: {stats['total_requests']}")
        print(f"   - 缓存命中数: {stats['cache_hits']}")
        print(f"   - 缓存命中率: {stats['cache_hit_rate']}")
        print(f"   - 平均处理时间: {stats['avg_processing_time']}")
        print(f"   - 吞吐量: {stats['texts_per_second']} 文本/秒")

        return True

    except Exception as e:
        print(f"❌ 缓存性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 text_embedding工具修复验证（方案1）")
    print("=" * 60)
    print("\n方案说明:")
    print("- 修改text_embedding_handler使用BGEEmbeddingService")
    print("- 修复athena_model_loader.py中的重复配置")
    print("- 使用BGE Large ZH v1.5模型（1024维）")

    results = []

    # 测试1: BGE服务
    results.append(("BGE嵌入服务", await test_bge_service()))

    # 测试2: text_embedding_handler
    results.append(("text_embedding_handler", await test_text_embedding_handler()))

    # 测试3: 批量嵌入
    results.append(("批量文本嵌入", await test_batch_embedding()))

    # 测试4: 缓存性能
    results.append(("缓存性能", await test_cache_performance()))

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！text_embedding工具修复成功（方案1）")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
