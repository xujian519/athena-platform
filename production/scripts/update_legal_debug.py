#!/usr/bin/env python3
"""
法律向量库更新 - 调试版本
"""

from __future__ import annotations
from datetime import datetime

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# 配置
COLLECTION_NAME = "unified_legal_laws"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

print("🔍 调试模式: 测试单个向量插入")

# 初始化客户端
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
print(f"✅ Qdrant连接成功: {QDRANT_HOST}:{QDRANT_PORT}")

# 检查集合
collections = client.get_collections().collections
collection_names = [c.name for c in collections]
print(f"📊 现有集合: {collection_names}")

if COLLECTION_NAME in collection_names:
    info = client.get_collection(COLLECTION_NAME)
    print(f"📊 集合 {COLLECTION_NAME} 当前点数: {info.points_count}")
    print(f"📊 向量维度: {info.config.params.vectors.size}")
    print(f"📊 距离度量: {info.config.params.vectors.distance}")

# 测试单个向量插入
print("\n🧪 测试插入单个向量点...")

# 创建测试向量
test_vector = np.random.rand(1024).astype(np.float32).tolist()
# 使用整数ID
test_id = int.from_bytes(b'test_001', byteorder='big')

# 创建payload
test_payload = {
    "text": "这是一个测试文本",
    "law_title": "测试法律",
    "law_date": "2025-01-11",
    "law_category_cn": "测试",
    "law_category_en": "test",
    "law_keywords": ["测试"],
    "chunk_index": 0,
    "section": "第一章",
    "file_path": "/test/path.md",
    "updated_at": datetime.now().isoformat()
}

print(f"向量类型: {type(test_vector)}")
print(f"向量长度: {len(test_vector)}")
print(f"向量前5个值: {test_vector[:5]}")

# 创建PointStruct
point = PointStruct(
    id=test_id,
    vector=test_vector,
    payload=test_payload
)

print("✅ PointStruct创建成功")
print(f"   点ID: {point.id}")
print(f"   向量类型: {type(point.vector)}")

# 尝试插入
try:
    print("\n⏳ 正在插入测试向量...")
    operation_info = client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point],
        wait=True
    )
    print("✅ 插入成功!")
    print(f"   操作状态: {operation_info.status}")

    # 验证插入
    updated_info = client.get_collection(COLLECTION_NAME)
    print(f"\n📊 集合更新后点数: {updated_info.points_count}")

except Exception as e:
    print(f"❌ 插入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 调试完成")
