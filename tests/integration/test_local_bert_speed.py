#!/usr/bin/env python3
"""
测试本地BERT模型快速加载
Test Fast Loading with Local BERT Models
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

async def test_local_bert_speed():
    """测试本地BERT模型加载速度"""
    print("🚀 测试本地BERT模型加载速度")
    print("=" * 50)

    try:
        from core.ai.nlp.bert_service import get_bert_service

        # 获取服务
        bert_service = await get_bert_service()

        # 本地模型列表
        local_models = [
            ("chinese_base", "BERT-Base-Chinese"),
            ("roberta_chinanews", "RoBERTa-ChinaNews"),
            ("legal_electra", "Chinese-Legal-ELECTRA")
        ]

        # 测试文本
        test_text = "这是一个测试文本，用于验证BERT编码功能。"

        total_time = 0
        success_count = 0

        for model_key, model_name in local_models:
            print(f"\n🔹 测试 {model_name}...")
            try:
                # 测试加载时间
                load_start = time.time()
                await bert_service.initialize_model(model_key)
                load_time = time.time() - load_start

                print("   ✅ 模型加载成功！")
                print(f"   ⏱️  加载时间: {load_time:.2f}秒")

                # 测试编码时间
                encode_start = time.time()
                result = await bert_service.encode(test_text, model_key)
                encode_time = time.time() - encode_start

                print(f"   ⚡ 编码时间: {encode_time:.3f}秒")

                if result.embeddings is not None:
                    print(f"   📏 向量维度: {len(result.embeddings) if len(result.embeddings.shape) == 1 else result.embeddings.shape}")
                    success_count += 1
                    total_time += (load_time + encode_time)

            except Exception as e:
                print(f"   ❌ 测试失败: {e}")

        # 总结
        print("\n" + "=" * 50)
        print("📊 测试总结:")
        print(f"   - 成功模型: {success_count}/{len(local_models)}")
        if success_count > 0:
            print(f"   - 平均总时间: {total_time/success_count:.2f}秒")
            print(f"   - 速度评估: {'🚀 快速' if total_time/success_count < 5 else '⚠️  较慢' if total_time/success_count < 10 else '🐌 缓慢'}")

        # 获取模型信息
        model_info = bert_service.get_model_info()
        print("\n📋 模型详情:")
        for key in ["chinese_base", "roberta_chinanews", "legal_electra"]:
            if key in model_info and isinstance(model_info[key], dict):
                info = model_info[key]
                print(f"   - {key}: {info.get('name', 'Unknown')}")
                print(f"     加载状态: {'✅' if info.get('loaded') else '❌'}")
                if info.get('load_time'):
                    print(f"     加载时间: {info['load_time']:.2f}秒")

        return success_count > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bert_vs_bge_speed():
    """对比BERT和BGE的速度"""
    print("\n🆚 BERT vs BGE 速度对比")
    print("-" * 30)

    test_text = "专利技术的创新性评估需要进行全面的技术分析。"

    try:
        # 测试BERT（使用本地模型）
        print("\n🔹 BERT性能测试...")
        from core.ai.nlp.bert_service import encode_with_general_bert

        bert_times = []
        for i in range(3):
            start = time.time()
            await encode_with_general_bert(test_text)
            bert_time = time.time() - start
            bert_times.append(bert_time)
            print(f"   第{i+1}次: {bert_time:.3f}秒")

        avg_bert = sum(bert_times) / len(bert_times)
        print(f"   BERT平均: {avg_bert:.3f}秒")

        # 测试BGE
        print("\n🔹 BGE性能测试...")
        from core.ai.embedding.unified_embedding_service import encode_for_document

        bge_times = []
        for i in range(3):
            start = time.time()
            await encode_for_document(test_text)
            bge_time = time.time() - start
            bge_times.append(bge_time)
            print(f"   第{i+1}次: {bge_time:.3f}秒")

        avg_bge = sum(bge_times) / len(bge_times)
        print(f"   BGE平均: {avg_bge:.3f}秒")

        # 对比
        print("\n📈 速度对比:")
        if avg_bge < avg_bert:
            speedup = avg_bert / avg_bge
            print(f"   BGE比BERT快 {speedup:.1f}x")
        else:
            slowdown = avg_bge / avg_bert
            print(f"   BERT比BGE快 {slowdown:.1f}x")

        print("\n💡 使用建议:")
        print("   - 文本理解任务: 使用BERT（分析深度更好）")
        print("   - 语义相似度任务: 使用BGE（向量质量更高）")

    except Exception as e:
        print(f"❌ 对比测试失败: {e}")

async def main():
    """主函数"""
    print("🤖 BERT速度优化测试")
    print("=" * 60)

    success = await test_local_bert_speed()

    if success:
        await test_bert_vs_bge_speed()

        print("\n" + "=" * 60)
        print("🎉 优化建议:")
        print("✅ 使用本地模型，避免下载等待")
        print("✅ 启用半精度推理和设备优化")
        print("✅ 根据任务类型选择合适模型")
        print("\n📌 下一步:")
        print("- 可以考虑预加载常用模型")
        print("- 使用模型缓存避免重复加载")
    else:
        print("\n❌ 本地模型测试失败")
        print("💡 建议检查:")
        print("1. 模型文件是否完整")
        print("2. 依赖是否正确安装")

if __name__ == "__main__":
    asyncio.run(main())
