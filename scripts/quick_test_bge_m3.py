#!/usr/bin/env python3
"""快速测试BGE-M3模型是否可用"""
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

print("=" * 60)
print("快速测试BGE-M3模型")
print("=" * 60)

# 测试1: 导入sentence_transformers
print("\n1. 测试sentence_transformers导入...")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence_transformers导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 加载BGE-M3模型
print("\n2. 测试BGE-M3模型加载...")
try:
    print("   ⏳ 正在加载BAAI/bge-m3...")
    model = SentenceTransformer('BAAI/bge-m3', device='cpu')
    print("✅ BGE-M3模型加载成功")
    print(f"   - 向量维度: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    sys.exit(1)

# 测试3: 生成嵌入
print("\n3. 测试文本嵌入...")
try:
    test_text = "这是一个测试文本"
    embedding = model.encode(test_text, show_progress_bar=False)
    print(f"✅ 文本嵌入成功")
    print(f"   - 向量维度: {len(embedding)}")
    print(f"   - 前5维: {embedding[:5]}")
except Exception as e:
    print(f"❌ 嵌入失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 所有测试通过！BGE-M3模型可用")
print("=" * 60)
