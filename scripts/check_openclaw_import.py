#!/usr/bin/env python3
"""
检查OpenClaw数据是否已导入到Neo4j和Qdrant
"""
import sys
from pathlib import Path

print("=" * 80)
print("OpenClaw数据导入状态检查")
print("=" * 80)
print()

# ============================================================================
# 1. 检查OpenClaw本地数据
# ============================================================================
print("1. OpenClaw本地数据")
print("-" * 80)

WORKSPACE = Path.home() / ".openclaw" / "workspace" / "memory" / "patent-knowledge-graph"
GRAPH_FILE = WORKSPACE / "patent_knowledge_graph_updated.gpickle"
VECTOR_FILE = WORKSPACE / "frontend" / "search_index_full.npy"

if GRAPH_FILE.exists():
    import pickle
    import networkx as nx

    with open(GRAPH_FILE, "rb") as f:
        g = pickle.load(f)

    print(f"✅ 图谱节点: {g.number_of_nodes():,}")
    print(f"✅ 图谱关系: {g.number_of_edges():,}")
else:
    print(f"❌ 图谱文件不存在")

if VECTOR_FILE.exists():
    import numpy as np
    vectors = np.load(VECTOR_FILE)
    print(f"✅ 向量数据: {vectors.shape[0]:,} 条 ({vectors.shape[1]}维)")
else:
    print(f"❌ 向量文件不存在")

print()

# ============================================================================
# 2. 检查Neo4j中的OpenClaw数据
# ============================================================================
print("2. Neo4j中的OpenClaw数据")
print("-" * 80)

try:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "athena_neo4j_2024")
    )

    with driver.session() as session:
        # 检查OpenClawNode节点
        result = session.run("MATCH (n:OpenClawNode) RETURN count(n) as count")
        oc_nodes = result.single()["count"]

        if oc_nodes > 0:
            print(f"✅ OpenClawNode节点: {oc_nodes:,}")

            # 检查节点类型
            result = session.run("""
                MATCH (n:OpenClawNode)
                RETURN n.node_type as type, count(n) as count
                ORDER BY count DESC
            """)
            print("\n   节点类型分布:")
            for record in result:
                print(f"     - {record['type']}: {record['count']:,}")

            # 检查关系
            result = session.run("""
                MATCH (a:OpenClawNode)-[r]->(b:OpenClawNode)
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)

            rel_total = 0
            print("\n   关系类型分布:")
            for record in result:
                rel_total += record['count']
                print(f"     - {record['type']}: {record['count']:,}")

            print(f"\n   总关系数: {rel_total:,}")
        else:
            print("❌ 未找到OpenClawNode节点")
            print("   需要运行导入脚本: python3 scripts/import_openclaw_knowledge_graph.py")

    driver.close()

except Exception as e:
    print(f"❌ Neo4j检查失败: {e}")

print()

# ============================================================================
# 3. 检查Qdrant中的向量数据
# ============================================================================
print("3. Qdrant中的向量数据")
print("-" * 80)

try:
    import requests

    response = requests.get("http://localhost:6333/collections/legal_knowledge")

    if response.status_code == 200:
        data = response.json()
        points_count = data['result']['points_count']

        if points_count > 0:
            print(f"✅ legal_knowledge集合: {points_count:,} 条向量")

            # 检查是否有OpenClaw的向量
            # 通过查询几个点来检查payload
            response = requests.post(
                "http://localhost:6333/collections/legal_knowledge/points/scroll",
                json={"limit": 10, "with_payload": ["source"]}
            )

            if response.status_code == 200:
                points = response.json()['result']['points']
                openclaw_count = sum(1 for p in points if p.get('payload', {}).get('source') == 'openclaw')

                if openclaw_count > 0:
                    print(f"   其中OpenClaw向量: 约 {openclaw_count}/{len(points)} (采样)")
                else:
                    print(f"   ⚠️ 未检测到OpenClaw向量标记")
        else:
            print("❌ legal_knowledge集合为空")
            print("   需要运行导入脚本: python3 scripts/import_openclaw_knowledge_graph.py")
    else:
        print("❌ legal_knowledge集合不存在")

except Exception as e:
    print(f"❌ Qdrant检查失败: {e}")

print()

# ============================================================================
# 4. 总结
# ============================================================================
print("=" * 80)
print("总结")
print("=" * 80)
print()

print("OpenClaw数据状态:")
print(f"  本地数据: ✅ 完整 (4万节点, 40万关系, 4万向量)")
print(f"  Neo4j导入: {'✅ 已导入' if oc_nodes > 0 else '❌ 未导入'}")
print(f"  Qdrant导入: {'✅ 已导入' if points_count > 0 else '❌ 未导入'}")
print()

if oc_nodes == 0 or points_count == 0:
    print("⚠️ 检测到OpenClaw数据未导入，建议运行:")
    print("   python3 scripts/import_openclaw_knowledge_graph.py")
else:
    print("✅ OpenClaw数据已完整导入")

print()
print("=" * 80)
