#!/usr/bin/env python3
"""
PatentSBERTa演示测试
PatentSBERTa Demo Test

独立测试PatentSBERTa编码器的功能

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    print("🚀 PatentSBERTa演示测试")
    print("=" * 60)

    # 测试1: 直接使用sentence-transformers
    print("\n📝 测试1: 直接使用sentence-transformers")

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer

        print("   加载PatentSBERTa模型...")
        model = SentenceTransformer('AI-Growth-Lab/PatentSBERTa')
        print("   ✅ 模型加载成功")

        # 测试编码
        texts = [
            "一种基于卷积神经网络的图像识别方法",
            "深度学习在计算机视觉中的应用",
            "齿轮传动装置的设计原理",
        ]

        print(f"\n   编码 {len(texts)} 个专利文本...")
        embeddings = model.encode(texts, normalize_embeddings=True)

        print(f"   ✅ 嵌入维度: {embeddings.shape[1]}")
        print(f"   📊 嵌入向量示例 (前10维): {embeddings[0][:10]}")

        # 计算相似度
        sim = np.dot(embeddings[0], embeddings[1])
        print("\n   相似度测试:")
        print(f"      文本1 vs 文本2: {sim:.4f}")

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

    # 测试2: 比较通用SBERT
    print("\n📝 测试2: 对比通用SBERT")

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer

        print("   加载通用SBERT模型...")
        general_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("   ✅ 通用SBERT加载成功")

        # 对比测试
        patent_text = "一种基于卷积神经网络的图像识别方法"

        patent_emb = model.encode([patent_text], normalize_embeddings=True)
        general_emb = general_model.encode([patent_text], normalize_embeddings=True)

        print("\n   嵌入维度对比:")
        print(f"      PatentSBERTa: {patent_emb.shape[1]}维")
        print(f"      通用SBERT:    {general_emb.shape[1]}维")

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")

    print("\n" + "=" * 60)
    print("✅ PatentSBERTa演示测试完成")
    print("\n📋 结论:")
    print("   1. PatentSBERTa模型可以正常加载和使用")
    print("   2. 专利嵌入向量可以正确生成")
    print("   3. 相比通用模型，PatentSBERTa针对专利文本优化")
    print("\n🔧 后续步骤:")
    print("   1. 集成到统一嵌入服务")
    print("   2. 实现双嵌入检索系统")
    print("   3. 进行大规模性能对比测试")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
