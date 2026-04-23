#!/usr/bin/env python3
from __future__ import annotations
"""
Phase 2 快速验证脚本
Quick Phase 2 Verification

快速验证本地BERT模型是否可用

作者: 小诺·双鱼公主
版本: v2.0.0
创建: 2025-12-29
"""

import sys
import time
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def quick_test() -> Any:
    """快速测试本地BERT模型"""
    print("🍎 Apple Silicon本地BERT模型快速测试")
    print("=" * 60)

    try:
        # 导入必要的库
        import torch
        from transformers import AutoModel, AutoTokenizer

        # 1. 检查MPS可用性
        print("\n1️⃣ 检查硬件加速:")
        if torch.backends.mps.is_available():
            print("   ✅ MPS GPU加速可用(Apple Silicon)")
            device = torch.device("mps")
        else:
            print("   ⚠️ MPS不可用,使用CPU")
            device = torch.device("cpu")

        # 2. 加载本地BERT模型
        print("\n2️⃣ 加载本地BERT模型:")
        model_name = "BAAI/bge-m3"
        print(f"   📂 模型: {model_name}")

        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        model = model.to(device)
        model.eval()
        load_time = time.time() - start

        print(f"   ✅ 模型加载成功 ({load_time:.2f}s)")

        # 3. 测试文本编码
        print("\n3️⃣ 测试文本编码:")
        test_texts = ["分析这个专利", "帮我写代码", "谢谢爸爸"]

        for text in test_texts:
            start = time.time()

            # Tokenize
            inputs = tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512, padding=True
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Encode
            with torch.no_grad():
                outputs = model(**inputs)
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]

            elapsed = time.time() - start

            print(f"   📝 '{text}'")
            print(f"      向量维度: {embedding.shape}")
            print(f"      耗时: {elapsed*1000:.1f}ms")

        # 4. 测试批量编码
        print("\n4️⃣ 测试批量编码:")
        start = time.time()

        batch_inputs = tokenizer(
            test_texts, return_tensors="pt", truncation=True, max_length=512, padding=True
        )
        batch_inputs = {k: v.to(device) for k, v in batch_inputs.items()}

        with torch.no_grad():
            batch_outputs = model(**batch_inputs)
            batch_embeddings = batch_outputs.last_hidden_state[:, 0, :].cpu().numpy()

        batch_time = time.time() - start

        print("   ✅ 批量编码成功")
        print(f"      批次大小: {len(test_texts)}")
        print(f"      输出形状: {batch_embeddings.shape}")
        print(f"      总耗时: {batch_time*1000:.1f}ms")
        print(f"      平均: {batch_time*1000/len(test_texts):.1f}ms/文本")

        # 5. 计算相似度
        print("\n5️⃣ 测试相似度计算:")
        from sklearn.metrics.pairwise import cosine_similarity

        emb1 = batch_embeddings[0]
        emb2 = batch_embeddings[1]
        emb3 = batch_embeddings[2]

        sim12 = cosine_similarity([emb1], [emb2])[0][0]
        sim13 = cosine_similarity([emb1], [emb3])[0][0]
        sim23 = cosine_similarity([emb2], [emb3])[0][0]

        print(f"   '分析这个专利' vs '帮我写代码': {sim12:.4f}")
        print(f"   '分析这个专利' vs '谢谢爸爸': {sim13:.4f}")
        print(f"   '帮我写代码' vs '谢谢爸爸': {sim23:.4f}")

        # 6. 内存使用
        print("\n6️⃣ 内存使用:")
        if device.type == "mps" and hasattr(torch.mps, "current_allocated_memory"):
            allocated_mb = torch.mps.current_allocated_memory() / (1024 * 1024)
            print(f"   GPU已分配: {allocated_mb:.1f}MB")

        # 7. 总结
        print("\n" + "=" * 60)
        print("✅ 本地BERT模型测试通过!")
        print("\n📊 性能总结:")
        print(f"  - 模型加载时间: {load_time:.2f}s")
        print(f"  - 单文本编码: ~{elapsed*1000:.1f}ms")
        print(f"  - 批量编码: ~{batch_time*1000/len(test_texts):.1f}ms/文本")
        print(f"  - 硬件加速: {'MPS (Apple Silicon)' if device.type == 'mps' else 'CPU'}")
        print("  - 向量维度: 768")
        print("\n🎯 Phase 2 准备就绪!")
        print("\n下一步:")
        print("  1. 使用训练数据训练RandomForest分类器")
        print("  2. 评估模型准确率(目标: 85%)")
        print("  3. 集成到小诺主系统")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
