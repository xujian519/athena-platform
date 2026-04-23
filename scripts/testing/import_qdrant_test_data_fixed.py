#!/usr/bin/env python3
"""
Qdrant基准测试数据导入脚本 - 修复版本
使用正确的REST API格式：直接传递points数组
"""

import random
import requests
from typing import List, Dict, Any

# Qdrant配置
QDRANT_URL = "http://localhost:16333"
TEST_DATA_SIZE = 10

# 集合配置
COLLECTIONS = [
    ("patent_rules_1024", 1024),
    ("legal_main", 1024),
    ("patent_legal", 1024),
    ("technical_terms_1024", 1024),
    ("case_analysis", 1024),
    ("patent_fulltext", 768),
    ("legal_qa", 768)
]


def generate_random_vector(size: int) -> List[float]:
    """生成指定维度的随机向量"""
    return [random.uniform(-1, 1) for _ in range(size)]


def generate_test_payload(collection_name: str, idx: int) -> Dict[str, Any]:
    """生成测试数据的payload"""
    base_payload = {
        "test_id": f"{collection_name}_test_{idx}",  # 在payload中保存原始ID
        "text": f"测试数据 {idx} - {collection_name}",
        "category": random.choice(["专利", "法律", "技术", "案例"]),
        "timestamp": "2026-04-18T22:00:00Z",
        "source": "benchmark_test"
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


def import_test_data(collection_name: str, vector_size: int) -> int:
    """向指定集合导入测试数据

    Args:
        collection_name: 集合名称
        vector_size: 向量维度

    Returns:
        成功导入的数据条数
    """

    print(f"\n📦 处理集合: {collection_name} ({vector_size}维)")

    # 生成测试数据
    # 注意: Qdrant 1.7.4的REST API只支持数字ID，不支持字符串ID
    points = []
    for idx in range(1, TEST_DATA_SIZE + 1):
        # 使用全局唯一的数字ID
        # 格式: {集合索引 * 10000 + idx}
        collection_idx = [name for name, _ in COLLECTIONS].index(collection_name)
        point_id = collection_idx * 10000 + idx

        point = {
            "id": point_id,
            "vector": generate_random_vector(vector_size),
            "payload": generate_test_payload(collection_name, idx)
        }
        points.append(point)

    # 使用正确的REST API格式
    # 格式: {"points": [...]}
    url = f"{QDRANT_URL}/collections/{collection_name}/points"
    headers = {"Content-Type": "application/json"}

    request_data = {"points": points}

    try:
        # PUT请求到 /collections/{name}/points
        response = requests.put(url, json=request_data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            operation_id = result.get('result', {}).get('operation_id', 0)
            status = result.get('result', {}).get('status', 'unknown')

            print(f"   ✅ 成功导入 {len(points)} 条测试数据")
            print(f"   📝 操作ID: {operation_id}, 状态: {status}")
            return len(points)
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
            return 0

    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return 0


def verify_collection_data(collection_name: str) -> int:
    """验证集合中的数据数量

    Args:
        collection_name: 集合名称

    Returns:
        集合中的数据条数
    """
    try:
        url = f"{QDRANT_URL}/collections/{collection_name}"
        response = requests.get(url)

        if response.status_code == 200:
            result = response.json()
            points_count = result.get('result', {}).get('points_count', 0)
            return points_count
        else:
            print(f"   ⚠️  获取集合信息失败: HTTP {response.status_code}")
            return 0

    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return 0


def main():
    """主函数"""

    print("=" * 70)
    print("Qdrant基准测试数据导入 - 修复版本")
    print("=" * 70)
    print(f"🎯 目标: 为{len(COLLECTIONS)}个集合各导入{TEST_DATA_SIZE}条测试数据")
    print(f"📊 总计: {len(COLLECTIONS) * TEST_DATA_SIZE}条测试数据")

    total_imported = 0

    # 导入数据
    for collection_name, vector_size in COLLECTIONS:
        imported = import_test_data(collection_name, vector_size)
        total_imported += imported

    print("\n" + "=" * 70)
    print(f"📊 总计导入 {total_imported} 条测试数据")
    print("=" * 70)

    # 验证结果
    print("\n🔍 验证导入结果...")
    print("-" * 70)

    verified_total = 0
    for collection_name, _ in COLLECTIONS:
        count = verify_collection_data(collection_name)
        verified_total += count

        status_icon = "✅" if count >= TEST_DATA_SIZE else "⚠️"
        print(f"   {status_icon} {collection_name:30s}: {count:3d} 条数据")

    print("-" * 70)
    print(f"📊 验证总计: {verified_total} 条数据")

    if verified_total == len(COLLECTIONS) * TEST_DATA_SIZE:
        print("\n🎉 所有测试数据导入成功！")
        return 0
    else:
        print(f"\n⚠️  部分数据导入失败: {verified_total}/{len(COLLECTIONS) * TEST_DATA_SIZE}")
        return 1


if __name__ == "__main__":
    exit(main())
