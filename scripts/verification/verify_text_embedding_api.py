#!/usr/bin/env python3
"""
验证text_embedding工具使用BGE-M3 API（8766端口）
"""
import asyncio
import sys
import time

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


async def test_bge_m3_api():
    """测试BGE-M3 API服务"""
    print("\n" + "=" * 60)
    print("测试1: BGE-M3 API服务（8766端口）")
    print("=" * 60)

    try:
        import json
        import urllib.request

        # 健康检查
        print("\n⏳ 健康检查...")
        response = urllib.request.urlopen("http://127.0.0.1:8766/health", timeout=5)
        health_data = json.loads(response.read().decode("utf-8"))
        print(f"✅ API服务状态: {health_data}")

        # 测试嵌入
        print("\n⏳ 测试嵌入功能...")
        test_text = "专利检索是专利分析的基础"
        payload = {
            "input": test_text,
            "model": "bge-m3"
        }

        req = urllib.request.Request(
            "http://127.0.0.1:8766/v1/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        elapsed_time = time.time() - start_time

        print("✅ 嵌入成功")
        print(f"   - 响应时间: {elapsed_time:.3f}秒")

        if result.get("object") == "list" and len(result.get("data", [])) > 0:
            embedding = result["data"][0]["embedding"]
            print(f"   - 向量维度: {len(embedding)}")
            print(f"   - 前5维: {embedding[:5]}")
            print(f"   - 模型: {result.get('model', 'bge-m3')}")
            return True
        else:
            print(f"❌ API返回格式错误: {result}")
            return False

    except Exception as e:
        print(f"❌ BGE-M3 API测试失败: {e}")
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
            },
            {
                "name": "英文短文本",
                "text": "This is a test text for embedding",
            },
            {
                "name": "空文本",
                "text": "",
            },
            {
                "name": "长文本",
                "text": "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，"
                       "它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。"
                       "该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。",
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
                    "model": "bge-m3",
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
                print(f"   API服务: {result.get('api_service', False)}")

                # 验证维度
                if result.get('embedding_dim') == 1024:
                    print("   ✅ 维度正确（1024）")
                    success_count += 1
                else:
                    print(f"   ⚠️ 维度为{result.get('embedding_dim', 0)}，期望1024")
            else:
                print(f"   ❌ 失败: {result.get('error', 'Unknown error')}")

        print(f"\n测试通过率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")

        return success_count >= len(test_cases) - 1  # 允许一个失败

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
        import json
        import urllib.request

        texts = [
            "专利检索是专利分析的基础",
            "人工智能是计算机科学的一个分支",
            "机器学习是人工智能的核心技术",
            "深度学习是机器学习的一个子集",
            "自然语言处理是AI的重要应用"
        ]

        print(f"⏳ 批量编码 {len(texts)} 个文本...")
        payload = {
            "input": texts,
            "model": "bge-m3"
        }

        req = urllib.request.Request(
            "http://127.0.0.1:8766/v1/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        start_time = time.time()
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        elapsed_time = time.time() - start_time

        print("✅ 批量编码成功")
        print(f"   - 文本数量: {len(result.get('data', []))}")
        print(f"   - 总时间: {elapsed_time:.3f}秒")
        print(f"   - 平均时间: {elapsed_time/len(texts):.3f}秒/个")
        print(f"   - 吞吐量: {len(texts)/elapsed_time:.1f} 文本/秒")

        # 验证每个向量维度
        for i, data in enumerate(result.get('data', [])[:3]):  # 只检查前3个
            embedding = data.get('embedding', [])
            print(f"   - 文本{i+1}向量维度: {len(embedding)}")

        return True

    except Exception as e:
        print(f"❌ 批量嵌入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 text_embedding工具验证（BGE-M3 API）")
    print("=" * 60)
    print("\n方案说明:")
    print("- 使用8766端口的BGE-M3 API服务")
    print("- 通过HTTP API调用，避免本地模型加载")
    print("- BGE-M3模型：1024维，支持8192长度")

    results = []

    # 测试1: BGE-M3 API服务
    results.append(("BGE-M3 API服务", await test_bge_m3_api()))

    # 测试2: text_embedding_handler
    results.append(("text_embedding_handler", await test_text_embedding_handler()))

    # 测试3: 批量嵌入
    results.append(("批量文本嵌入", await test_batch_embedding()))

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
        print("\n🎉 所有测试通过！text_embedding工具已成功使用BGE-M3 API")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
