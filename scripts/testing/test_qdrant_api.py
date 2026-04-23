#!/usr/bin/env python3
"""
直接测试Qdrant客户端API
"""

from qdrant_client import QdrantClient

client = QdrantClient(host='localhost', port=6333)

# 获取集合列表
collections = client.get_collections().collections
print("所有集合:")
for coll in collections:
    print(f"  - {coll.name}")

# 测试query_points API
print("\n测试query_points API:")
try:
    # 使用简单的方式调用query_points
    result = client.query_points(
        collection_name="patent_rules_1024",
        query=[0.1] * 1024,  # 测试向量
        limit=5
    )
    print("✅ query_points工作正常")
    print(f"   结果数: {len(result.points)}")
except Exception as e:
    print(f"❌ query_points失败: {e}")

# 测试其他API
print("\n测试recommend API:")
try:
    result = client.recommend(
        collection_name="patent_rules_1024",
        limit=5
    )
    print("✅ recommend工作正常")
    print(f"   结果数: {len(result)}")
except Exception as e:
    print(f"❌ recommend失败: {e}")

# 测试search API
print("\n测试search API:")
try:
    result = client.search(
        collection_name="patent_rules_1024",
        query_vector=[0.1] * 1024,
        limit=5
    )
    print("✅ search工作正常")
    print(f"   结果数: {len(result)}")
except Exception as e:
    print(f"❌ search失败: {e}")
