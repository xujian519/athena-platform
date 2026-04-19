#!/usr/bin/env python3
"""
Qdrant向量数据库直接测试
"""

from __future__ import annotations
import time
from typing import Any

import requests


def test_qdrant() -> Any:
    """测试Qdrant连接和功能"""
    print("🔍 测试Qdrant向量数据库...")

    try:
        # 测试1: 健康检查
        response = requests.get('http://localhost:6333/health', timeout=10)
        if response.status_code == 200:
            print("✅ Qdrant健康检查通过")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return

        # 测试2: 获取集合列表
        response = requests.get('http://localhost:6333/collections', timeout=10)
        if response.status_code == 200:
            collections = response.json()
            count = len(collections.get('result', {}).get('collections', []))
            print(f"✅ 集合列表获取成功，共 {count} 个集合")

            # 显示前5个集合
            for _i, collection in enumerate(collections.get('result', {}).get('collections', [])[:5]):
                print(f"   📁 {collection['name']}")
        else:
            print(f"❌ 集合列表获取失败: {response.status_code}")

        # 测试3: 创建测试集合
        test_collection = f"storage_test_{int(time.time())}"
        collection_config = {
            "vectors": {
                "size": 768,
                "distance": "Cosine"
            }
        }

        response = requests.put(
            f'http://localhost:6333/collections/{test_collection}',
            json=collection_config,
            timeout=10
        )

        if response.status_code in [200, 201]:
            print(f"✅ 测试集合创建成功: {test_collection}")

            # 测试4: 插入向量数据
            test_points = [
                {
                    "id": 1,
                    "vector": [0.1] * 768,
                    "payload": {
                        "text": "测试文档1",
                        "category": "test"
                    }
                },
                {
                    "id": 2,
                    "vector": [0.2] * 768,
                    "payload": {
                        "text": "测试文档2",
                        "category": "test"
                    }
                }
            ]

            response = requests.put(
                f'http://localhost:6333/collections/{test_collection}/points',
                json={"points": test_points},
                timeout=10
            )

            if response.status_code == 200:
                print("✅ 向量数据插入成功")

                # 测试5: 向量搜索
                search_vector = [0.15] * 768
                response = requests.post(
                    f'http://localhost:6333/collections/{test_collection}/search',
                    json={
                        "vector": search_vector,
                        "limit": 2
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    search_result = response.json()
                    results = search_result.get('result', [])
                    print(f"✅ 向量搜索成功，找到 {len(results)} 个结果")

                    for result in results:
                        print(f"   🎯 ID: {result['id']}, 相似度: {result['score']:.4f}")

                # 清理测试数据
                response = requests.delete(f'http://localhost:6333/collections/{test_collection}', timeout=10)
                if response.status_code == 200:
                    print(f"✅ 测试集合已清理: {test_collection}")

            else:
                print(f"❌ 向量数据插入失败: {response.status_code}")
        else:
            print(f"❌ 测试集合创建失败: {response.status_code}")

        print("\n🎉 Qdrant向量数据库验证完成！")

    except Exception as e:
        print(f"❌ Qdrant测试异常: {e}")

if __name__ == "__main__":
    test_qdrant()
