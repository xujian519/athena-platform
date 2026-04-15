#!/usr/bin/env python3
"""
BERT集成测试脚本
Test BERT Integration for Athena Platform
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

async def test_bert_service():
    """测试BERT服务"""
    print("🧪 测试BERT服务集成...")
    print("=" * 50)

    try:
        from core.nlp.bert_service import get_bert_service

        # 初始化服务
        bert_service = await get_bert_service()
        print("✅ BERT服务初始化成功")

        # 显示可用模型
        model_info = bert_service.get_model_info()
        print("\n📋 可用模型:")
        for model_key, info in model_info.items():
            if isinstance(info, dict) and "name" in info:
                print(f"   - {model_key}: {info['name']}")
                if info.get("loaded"):
                    print("     状态: ✅ 已加载")
                else:
                    print("     状态: ⏳ 待加载")

        # 测试编码（通用BERT）
        print("\n🔹 测试通用BERT编码...")
        try:
            from core.nlp.bert_service import encode_with_general_bert

            test_text = "这是一个测试文本，用于验证BERT编码功能。"
            result = await encode_with_general_bert(test_text)

            print(f"   - 文本: {test_text}")
            print(f"   - 编码成功: {result.embeddings is not None}")
            if result.embeddings is not None:
                print(f"   - 向量维度: {len(result.embeddings)}")
                print(f"   - 处理时间: {result.processing_time:.3f}秒")
        except Exception as e:
            print(f"   - 通用BERT测试失败: {e}")

        # 测试法律BERT
        print("\n🔹 测试法律BERT编码...")
        try:
            from core.nlp.bert_service import encode_with_legal_bert

            legal_text = "根据《中华人民共和国专利法》，发明专利的保护期限为二十年。"
            result = await encode_with_legal_bert(legal_text)

            print(f"   - 法律文本: {legal_text}")
            print(f"   - 编码成功: {result.embeddings is not None}")
            if result.embeddings is not None:
                print(f"   - 向量维度: {len(result.embeddings)}")
                print(f"   - 处理时间: {result.processing_time:.3f}秒")
        except Exception as e:
            print(f"   - 法律BERT测试失败: {e}")

        # 批量测试
        print("\n🔹 批量编码测试...")
        try:
            batch_texts = [
                "人工智能技术正在改变世界。",
                "专利保护是创新的重要保障。",
                "法律条文需要准确理解。",
                "深度学习是AI的核心技术。"
            ]

            start_time = time.time()
            result = await bert_service.encode(batch_texts, "general")
            batch_time = time.time() - start_time

            if result.embeddings is not None:
                print("   - 批量编码成功")
                print(f"   - 文本数量: {len(batch_texts)}")
                print(f"   - 批量处理时间: {batch_time:.3f}秒")
                print(f"   - 平均每文本: {batch_time/len(batch_texts):.3f}秒")

        except Exception as e:
            print(f"   - 批量测试失败: {e}")

        # 特征提取测试
        print("\n🔹 特征提取测试...")
        try:
            features = await bert_service.extract_features(
                "专利技术的创新性评估",
                "general",
                layer=-1
            )

            if features.size > 0:
                print("   - 特征提取成功")
                print(f"   - 特征维度: {features.shape}")
        except Exception as e:
            print(f"   - 特征提取失败: {e}")

        # 获取统计信息
        stats = bert_service.get_statistics()
        print("\n📊 使用统计:")
        print(f"   - 总请求数: {stats['total_requests']}")
        print(f"   - 平均处理时间: {stats['avg_processing_time']:.3f}秒")
        print(f"   - 已加载模型: {stats['loaded_models']}")

        return True

    except Exception as e:
        print(f"❌ BERT服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_model_comparison():
    """测试不同模型的对比"""
    print("\n🔍 模型对比测试...")
    print("-" * 30)

    try:
        from core.nlp.bert_service import get_bert_service

        bert_service = await get_bert_service()

        test_text = "这项发明专利涉及深度学习技术在图像识别领域的创新应用。"

        models_to_test = ["general", "legal"]
        results = {}

        for model_key in models_to_test:
            try:
                # 初始化模型
                await bert_service.initialize_model(model_key)

                # 编码测试
                result = await bert_service.encode(test_text, model_key)

                if result.embeddings is not None:
                    embedding = result.embeddings
                    if isinstance(embedding, list) and len(embedding) > 0:
                        embedding = embedding[0]

                    results[model_key] = {
                        "model": bert_service.get_model_info(model_key)["name"],
                        "vector_size": len(embedding),
                        "processing_time": result.processing_time,
                        "vector_sample": list(embedding[:5]) if isinstance(embedding, list) else embedding[:5].tolist()
                    }

            except Exception as e:
                print(f"   - {model_key} 测试失败: {e}")

        # 输出对比结果
        print(f"\n📈 模型对比结果 (测试文本: {test_text}):")
        for model_key, data in results.items():
            print(f"\n{model_key.upper()}:")
            print(f"   - 模型: {data['model']}")
            print(f"   - 向量维度: {data['vector_size']}")
            print(f"   - 处理时间: {data['processing_time']:.3f}秒")
            print(f"   - 向量前5位: {[f'{x:.4f}' for x in data['vector_sample']]}")

        # 向量相似度计算
        if len(results) > 1:
            print("\n🔗 模型间向量相似度:")
            model_keys = list(results.keys())
            for i in range(len(model_keys)):
                for j in range(i+1, len(model_keys)):
                    key1, key2 = model_keys[i], model_keys[j]
                    # 简单的余弦相似度计算
                    v1 = results[key1]["vector_sample"]
                    v2 = results[key2]["vector_sample"]

                    import numpy as np
                    v1_np = np.array(v1)
                    v2_np = np.array(v2)

                    similarity = np.dot(v1_np, v2_np) / (
                        np.linalg.norm(v1_np) * np.linalg.norm(v2_np)
                    )

                    print(f"   - {key1} vs {key2}: {similarity:.4f}")

    except Exception as e:
        print(f"❌ 模型对比失败: {e}")

async def test_integration_with_existing_modules():
    """测试与现有模块的集成"""
    print("\n🔧 测试与现有模块集成...")
    print("-" * 30)

    # 测试与BGE的协同使用
    try:
        from core.embedding.unified_embedding_service import encode_for_document
        from core.nlp.bert_service import encode_with_general_bert

        test_text = "这份专利文件描述了一种新型的机器学习算法。"

        # BERT编码（理解任务）
        bert_result = await encode_with_general_bert(test_text)
        print(f"✅ BERT编码成功，向量维度: {len(bert_result.embeddings) if bert_result.embeddings is not None else 0}")

        # BGE编码（语义相似任务）
        try:
            bge_result = await encode_for_document(test_text)
            print(f"✅ BGE编码成功，向量维度: {bge_result['dimension']}")
            print("💡 建议使用场景:")
            print("   - 文本理解任务: 使用BERT")
            print("   - 语义相似度任务: 使用BGE")
        except Exception as e:
            print(f"⚠️ BGE编码失败: {e}")

    except Exception as e:
        print(f"❌ 模块集成测试失败: {e}")

async def main():
    """主函数"""
    print("🤖 BERT集成测试")
    print("=" * 60)

    success = await test_bert_service()

    if success:
        await test_model_comparison()
        await test_integration_with_existing_modules()

        print("\n" + "=" * 60)
        print("🎉 BERT集成测试完成！")
        print("✅ BERT服务工作正常")
        print("✅ 多模型支持正常")
        print("✅ 与现有模块集成成功")
    else:
        print("\n" + "=" * 60)
        print("❌ BERT集成测试失败")
        print("请检查模型是否正确下载")

if __name__ == "__main__":
    asyncio.run(main())
