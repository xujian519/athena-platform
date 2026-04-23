#!/usr/bin/env python3
"""
使用scroll方法测试Qdrant集合
"""

import numpy as np
from qdrant_client import QdrantClient

client = QdrantClient(host='localhost', port=6333)

# 测试scroll方法
print("测试scroll方法获取patent_rules_1024集合数据:")
try:
    result = client.scroll(
        collection_name="patent_rules_1024",
        limit=10,
        with_payload=True,
        with_vectors=True
    )

    points = result[0]  # points
    print("✅ scroll方法正常工作")
    print(f"   找到 {len(points)} 个点")

    if points:
        print("\n第一个点的信息:")
        point = points[0]
        print(f"  ID: {point.id}")
        print(f"  向量维度: {len(point.vector) if hasattr(point.vector, '__len__') else 'unknown'}")
        print(f"  Payload: {point.payload}")

    # 如果有数据，尝试简单的余弦相似度搜索
    if points:
        print("\n尝试手动相似度计算:")
        query_vector = np.random.rand(1024)  # 随机查询向量

        similarities = []
        for point in points[:5]:  # 只计算前5个点
            if hasattr(point.vector, '__len__'):
                vector = np.array(point.vector)
                # 余弦相似度
                similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
                similarities.append({
                    "id": str(point.id),
                    "score": float(similarity),
                    "payload": point.payload
                })

        # 按相似度排序
        similarities.sort(key=lambda x: x["score"], reverse=True)

        print("✅ 手动相似度计算成功")
        for i, item in enumerate(similarities[:3], 1):
            print(f"  {i}. ID: {item['id']}, Score: {item['score']:.4f}")

except Exception as e:
    print(f"❌ scroll失败: {e}")
    import traceback
    traceback.print_exc()
