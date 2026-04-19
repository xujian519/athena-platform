#!/usr/bin/env python3
"""
Qdrant基准测试数据导入脚本 v3
使用正确的Qdrant REST API格式
"""

import random
import requests
import json

# Qdrant配置
QDRANT_URL = "http://localhost:16333"
TEST_DATA_SIZE = 10


def generate_test_data(collection_name: str, vector_size: int):
    """生成测试数据"""
    points = []

    for idx in range(1, TEST_DATA_SIZE + 1):
        # 生成向量
        if vector_size == 1024:
            vector = [random.uniform(-1, 1) for _ in range(1024)]
        else:
            vector = [random.uniform(-1, 1) for _ in range(768)]

        # 生成payload
        payload = {
            "text": f"测试数据 {idx}",
            "category": random.choice(["专利", "法律", "技术"]),
            "source": "benchmark_test"
        }

        point = {
            "id": f"{collection_name}_test_{idx}",
            "vector": vector,
            "payload": payload
        }
        points.append(point)

    return points


def import_to_collection(collection_name: str):
    """导入数据到指定集合"""

    # 先获取集合信息以确定向量维度
    try:
        response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
        response.raise_for_status()
        collection_info = response.json()

        vectors_config = collection_info['result']['config']['params']['vectors']
        vector_size = vectors_config['size']

        print(f"\n📦 处理集合: {collection_name} ({vector_size}维)")

        # 生成测试数据
        points = generate_test_data(collection_name, vector_size)

        # 构建插入请求
        # Qdrant REST API格式: {"points": [...]}
        insert_data = {"points": points}

        # 发送PUT请求
        url = f"{QDRANT_URL}/collections/{collection_name}/points"
        headers = {"Content-Type": "application/json"}

        response = requests.put(url, json=insert_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            uploaded = result['status'].get('updated', 0)
            print(f"   ✅ 成功导入 {uploaded} 条测试数据")
            return uploaded
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return 0

    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return 0


def verify_data():
    """验证导入结果"""
    print("\n🔍 验证导入结果...")

    collections = [
        "patent_rules_1024",
        "legal_main",
        "patent_legal",
        "technical_terms_1024",
        "case_analysis",
        "patent_fulltext",
        "legal_qa"
    ]

    total = 0
    for collection_name in collections:
        try:
            response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
            if response.status_code == 200:
                count = response.json()['result']['points_count']
                print(f"   ✅ {collection_name}: {count} 条数据")
                total += count
            else:
                print(f"   ⚠️  {collection_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {collection_name}: {e}")

    return total


def main():
    print("=" * 70)
    print("Qdrant基准测试数据导入 v3")
    print("=" * 70)

    collections = [
        ("patent_rules_1024", 1024),
        ("legal_main", 1024),
        ("patent_legal", 1024),
        ("technical_terms_1024", 1024),
        ("case_analysis", 1024),
        ("patent_fulltext", 768),
        ("legal_qa", 768)
    ]

    total = 0
    for collection_name, _ in collections:
        imported = import_to_collection(collection_name)
        total += imported

    print("\n" + "=" * 70)
    print(f"📊 总计导入 {total} 条测试数据")
    print("=" * 70)

    # 验证
    actual_total = verify_data()
    print(f"\n✅ 实际验证: {actual_total} 条数据")


if __name__ == "__main__":
    main()
