#!/usr/bin/env python3
"""
Qdrant基准测试数据导入脚本 v2
简化版本，直接使用REST API
"""

import random
import requests
import json

# Qdrant配置
QDRANT_URL = "http://localhost:16333"
TEST_DATA_SIZE = 10


def generate_random_text(length: int = 50) -> str:
    """生成随机中文文本"""
    words = ['人工智能', '专利', '法律', '创新', '技术', '发明', '申请', '审查',
             '权利', '要求', '创造性', '新颖性', '实用性', '公开', '实施',
             '方法', '系统', '装置', '算法', '数据', '处理', '分析', '模型']
    return ' '.join(random.choices(words, k=length))


def generate_1024_vector() -> list:
    """生成1024维测试向量"""
    return [random.uniform(-1, 1) for _ in range(1024)]


def generate_768_vector() -> list:
    """生成768维测试向量"""
    return [random.uniform(-1, 1) for _ in range(768)]


def import_test_data_to_collection(collection_name: str, vector_size: int):
    """向指定集合导入测试数据"""

    # 生成测试数据
    points = []
    for idx in range(1, TEST_DATA_SIZE + 1):
        if vector_size == 1024:
            vector = generate_1024_vector()
        else:
            vector = generate_768_vector()

        payload = {
            "id": f"test_{idx}",
            "text": generate_random_text(50),
            "category": random.choice(["专利", "法律", "技术", "案例"]),
            "timestamp": "2026-04-18T22:00:00Z",
            "source": "test_data"
        }

        point = {
            "id": f"{collection_name}_{idx}",
            "vector": vector,
            "payload": payload
        }
        points.append(point)

    # 使用REST API插入数据
    url = f"{QDRANT_URL}/collections/{collection_name}/points"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.put(url, json=points, headers=headers)
        response.raise_for_status()

        result = response.json()
        status = result.get('status', {})
        uploaded = status.get('updated', 0)

        print(f"   ✅ 成功导入 {uploaded} 条数据")
        return uploaded

    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return 0


def verify_collection_data(collection_name: str):
    """验证集合中的数据数量"""
    try:
        url = f"{QDRANT_URL}/collections/{collection_name}"
        response = requests.get(url)
        response.raise_for_status()

        result = response.json()
        result_data = result.get('result', {})
        points_count = result_data.get('points_count', 0)

        return points_count

    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return 0


def main():
    """主函数"""

    collections_config = [
        {"name": "patent_rules_1024", "size": 1024},
        {"name": "legal_main", "size": 1024},
        {"name": "patent_legal", "size": 1024},
        {"name": "technical_terms_1024", "size": 1024},
        {"name": "case_analysis", "size": 1024},
        {"name": "patent_fulltext", "size": 768},
        {"name": "legal_qa", "size": 768}
    ]

    print("=" * 70)
    print("Qdrant基准测试数据导入 v2")
    print("=" * 70)

    total_imported = 0

    for config in collections_config:
        collection_name = config["name"]
        vector_size = config["size"]

        print(f"\n📦 处理集合: {collection_name} ({vector_size}维)")

        imported = import_test_data_to_collection(collection_name, vector_size)
        total_imported += imported

    print("\n" + "=" * 70)
    print(f"📊 总计导入 {total_imported} 条测试数据")
    print("=" * 70)

    # 验证结果
    print("\n🔍 验证导入结果...")
    for config in collections_config:
        collection_name = config["name"]
        count = verify_collection_data(collection_name)
        print(f"   ✅ {collection_name}: {count} 条数据")


if __name__ == "__main__":
    main()
