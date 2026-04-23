#!/usr/bin/env python3
"""
Qdrant基准测试数据导入脚本
为各个Qdrant集合导入测试向量数据
"""

import random

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Qdrant配置
QDRANT_HOST = "localhost"
QDRANT_PORT = 16333

# 测试数据配置
TEST_DATA_SIZE = 10  # 每个集合导入10条测试数据


def generate_random_text(length: int = 50) -> str:
    """生成随机文本"""
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


def generate_test_payload(collection_name: str, idx: int) -> dict:
    """生成测试数据的payload"""
    base_payload = {
        "id": f"test_{idx}",
        "text": generate_random_text(50),
        "category": random.choice(["专利", "法律", "技术", "案例"]),
        "timestamp": "2026-04-18T22:00:00Z",
        "source": "test_data"
    }

    # 根据不同集合添加特定字段
    if "patent_rules" in collection_name:
        base_payload.update({
            "rule_type": random.choice(["创造性", "新颖性", "实用性"]),
            "article": random.choice(["第22条", "第26条", "第9条"])
        })
    elif "legal" in collection_name:
        base_payload.update({
            "law_type": random.choice(["专利法", "民法典", "刑法"]),
            "chapter": f"第{random.randint(1, 10)}章"
        })
    elif "technical" in collection_name:
        base_payload.update({
            "tech_field": random.choice(["人工智能", "区块链", "物联网"]),
            "application": random.choice(["医疗", "金融", "教育"])
        })

    return base_payload


def import_test_data():
    """导入测试数据到Qdrant"""

    # 初始化Qdrant客户端
    client = QdrantClient(
        url=f"http://{QDRANT_HOST}:{QDRANT_PORT}",
        prefer_grpc=False,
        check_compatibility=False
    )

    # 定义集合配置
    collections_config = [
        {
            "name": "patent_rules_1024",
            "vector_size": 1024,
            "vector_generator": generate_1024_vector
        },
        {
            "name": "legal_main",
            "vector_size": 1024,
            "vector_generator": generate_1024_vector
        },
        {
            "name": "patent_legal",
            "vector_size": 1024,
            "vector_generator": generate_1024_vector
        },
        {
            "name": "technical_terms_1024",
            "vector_size": 1024,
            "vector_generator": generate_1024_vector
        },
        {
            "name": "case_analysis",
            "vector_size": 1024,
            "vector_generator": generate_1024_vector
        },
        {
            "name": "patent_fulltext",
            "vector_size": 768,
            "vector_generator": generate_768_vector
        },
        {
            "name": "legal_qa",
            "vector_size": 768,
            "vector_generator": generate_768_vector
        }
    ]

    print("=" * 70)
    print("Qdrant基准测试数据导入")
    print("=" * 70)

    total_imported = 0

    for config in collections_config:
        collection_name = config["name"]
        vector_size = config["vector_size"]
        vector_generator = config["vector_generator"]

        print(f"\n📦 处理集合: {collection_name} ({vector_size}维)")

        # 生成测试数据
        points = []
        for idx in range(1, TEST_DATA_SIZE + 1):
            vector = vector_generator()
            payload = generate_test_payload(collection_name, idx)

            point = PointStruct(
                id=f"{collection_name}_{idx}",
                vector=vector,
                payload=payload
            )
            points.append(point)

        # 批量插入数据
        try:
            operation_info = client.upsert(
                collection_name=collection_name,
                points=points
            )

            print(f"   ✅ 成功导入 {operation_info.upserted_count} 条数据")
            total_imported += operation_info.upserted_count

        except Exception as e:
            print(f"   ❌ 导入失败: {e}")

    print("\n" + "=" * 70)
    print(f"📊 总计导入 {total_imported} 条测试数据")
    print("=" * 70)

    # 验证导入结果
    print("\n🔍 验证导入结果...")
    for config in collections_config:
        collection_name = config["name"]
        try:
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count
            print(f"   ✅ {collection_name}: {points_count} 条数据")
        except Exception as e:
            print(f"   ❌ {collection_name}: 验证失败 - {e}")


if __name__ == "__main__":
    import_test_data()
