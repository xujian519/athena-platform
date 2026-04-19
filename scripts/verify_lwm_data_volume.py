#!/usr/bin/env python3
"""
法律世界模型数据量验证脚本
Legal World Model Data Volume Verification
"""

import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
import json

print("=" * 80)
print("法律世界模型数据量验证")
print("=" * 80)
print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 存储结果
results = {}

# ============================================================================
# 1. Neo4j 数据量检查
# ============================================================================
print("1. Neo4j 知识图谱数据量")
print("-" * 80)

try:
    from neo4j import GraphDatabase

    URI = "bolt://localhost:7687"
    AUTH = ("neo4j", "athena_neo4j_2024")

    driver = GraphDatabase.driver(URI, auth=AUTH)

    with driver.session() as session:
        # 检查节点数量
        node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
        print(f"  节点总数: {node_count:,}")

        # 检查关系数量
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        print(f"  关系总数: {rel_count:,}")

        # 检查节点类型分布
        node_types = session.run("""
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
        """)
        print("\n  节点类型分布:")
        has_nodes = False
        for record in node_types:
            labels = record["labels"]
            count = record["count"]
            if labels:
                label_str = ", ".join(labels)
                print(f"    - {label_str}: {count:,}")
                has_nodes = True

        if not has_nodes:
            print("    ⚠️  暂无节点数据")

        # 检查关系类型分布
        rel_types = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        print("\n  关系类型分布:")
        has_rels = False
        for record in rel_types:
            rel_type = record["type"]
            count = record["count"]
            print(f"    - {rel_type}: {count:,}")
            has_rels = True

        if not has_rels:
            print("    ⚠️  暂无关系数据")

    driver.close()

    results["Neo4j"] = {
        "status": "✅ 正常",
        "nodes": node_count,
        "relationships": rel_count,
        "has_data": node_count > 0
    }

except Exception as e:
    print(f"  ❌ Neo4j连接失败: {e}")
    results["Neo4j"] = {
        "status": "❌ 失败",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 2. Qdrant 数据量检查
# ============================================================================
print("2. Qdrant 向量数据库数据量")
print("-" * 80)

try:
    import requests

    QDRANT_URL = "http://localhost:6333"

    # 获取所有集合
    response = requests.get(f"{QDRANT_URL}/collections")
    collections_data = response.json()

    if collections_data["status"] == "ok":
        collections = collections_data["result"]["collections"]
        print(f"  集合总数: {len(collections)}")

        total_points = 0
        collection_details = []

        for collection in collections:
            collection_name = collection["name"]
            # 获取集合详情
            detail_response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
            detail_data = detail_response.json()

            if detail_data["status"] == "ok":
                points_count = detail_data["result"]["points_count"]
                vector_size = detail_data["result"]["config"]["params"]["vectors"]["size"]
                total_points += points_count

                collection_details.append({
                    "name": collection_name,
                    "points": points_count,
                    "vector_size": vector_size
                })

                print(f"\n  集合: {collection_name}")
                print(f"    - 数据点数量: {points_count:,}")
                print(f"    - 向量维度: {vector_size}")

        print(f"\n  总数据点: {total_points:,}")

        results["Qdrant"] = {
            "status": "✅ 正常",
            "collections": len(collections),
            "total_points": total_points,
            "details": collection_details,
            "has_data": total_points > 0
        }
    else:
        print(f"  ❌ Qdrant API错误")
        results["Qdrant"] = {
            "status": "❌ 失败",
            "has_data": False
        }

except Exception as e:
    print(f"  ❌ Qdrant连接失败: {e}")
    results["Qdrant"] = {
        "status": "❌ 失败",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 3. PostgreSQL 数据量检查（如果配置了）
# ============================================================================
print("3. PostgreSQL 结构化数据库数据量")
print("-" * 80)

try:
    import psycopg2

    # 从环境变量或配置读取
    PG_HOST = "localhost"
    PG_PORT = 5432
    PG_USER = "athena"
    PG_PASSWORD = "athena_pg_2024"
    PG_DATABASE = "athena"

    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DATABASE
    )

    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("""
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)

    tables = cursor.fetchall()

    if tables:
        print(f"  数据表总数: {len(tables)}")
        print("\n  表数据量:")

        total_rows = 0
        for schema, table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            total_rows += count
            print(f"    - {table}: {count:,} 行")

        print(f"\n  总记录数: {total_rows:,}")

        results["PostgreSQL"] = {
            "status": "✅ 正常",
            "tables": len(tables),
            "total_rows": total_rows,
            "has_data": total_rows > 0
        }
    else:
        print("  ⚠️  未找到数据表")
        results["PostgreSQL"] = {
            "status": "⚠️  无表",
            "has_data": False
        }

    cursor.close()
    conn.close()

except Exception as e:
    print(f"  ⚠️  PostgreSQL未配置或连接失败: {e}")
    results["PostgreSQL"] = {
        "status": "⚠️  未配置",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 4. 本地文件数据检查
# ============================================================================
print("4. 本地文件数据")
print("-" * 80)

import os

# 检查数据目录
data_dirs = [
    "data/legal_knowledge",
    "data/patent_data",
    "data/case_law",
    "models/legal_world_model"
]

total_files = 0
total_size = 0

for data_dir in data_dirs:
    if os.path.exists(data_dir):
        file_count = 0
        dir_size = 0
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    file_count += 1
                    dir_size += os.path.getsize(file_path)

        total_files += file_count
        total_size += dir_size

        size_mb = dir_size / (1024 * 1024)
        print(f"  📁 {data_dir}: {file_count} 文件, {size_mb:.2f} MB")
    else:
        print(f"  📁 {data_dir}: 不存在")

print(f"\n  总文件数: {total_files}")
print(f"  总大小: {total_size / (1024 * 1024):.2f} MB")

results["本地文件"] = {
    "status": "✅ 正常" if total_files > 0 else "⚠️  无数据",
    "files": total_files,
    "size_mb": total_size / (1024 * 1024),
    "has_data": total_files > 0
}

print()

# ============================================================================
# 5. 数据量总结
# ============================================================================
print("=" * 80)
print("数据量总结")
print("=" * 80)

print(f"\n数据库状态:")
print(f"  Neo4j:       {results.get('Neo4j', {}).get('status', '未知')}")
print(f"  Qdrant:      {results.get('Qdrant', {}).get('status', '未知')}")
print(f"  PostgreSQL:  {results.get('PostgreSQL', {}).get('status', '未知')}")
print(f"  本地文件:    {results.get('本地文件', {}).get('status', '未知')}")

print(f"\n数据量统计:")
if "Neo4j" in results:
    neo4j_data = results["Neo4j"]
    if neo4j_data.get("has_data"):
        print(f"  Neo4j节点:      {neo4j_data.get('nodes', 0):,}")
        print(f"  Neo4j关系:      {neo4j_data.get('relationships', 0):,}")
    else:
        print(f"  Neo4j:          暂无数据")

if "Qdrant" in results:
    qdrant_data = results["Qdrant"]
    if qdrant_data.get("has_data"):
        print(f"  Qdrant集合:     {qdrant_data.get('collections', 0)}")
        print(f"  Qdrant数据点:   {qdrant_data.get('total_points', 0):,}")
    else:
        print(f"  Qdrant:         暂无数据")

if "PostgreSQL" in results:
    pg_data = results["PostgreSQL"]
    if pg_data.get("has_data"):
        print(f"  PostgreSQL表:   {pg_data.get('tables', 0)}")
        print(f"  PostgreSQL记录: {pg_data.get('total_rows', 0):,}")
    else:
        print(f"  PostgreSQL:     暂无数据或未配置")

print(f"\n总体评估:")
has_any_data = any(r.get("has_data", False) for r in results.values())

if has_any_data:
    # 统计有数据的数据库
    data_sources = [name for name, data in results.items() if data.get("has_data")]

    if len(data_sources) >= 3:
        print("  ✅ 数据完整 - 所有数据源都有数据")
    elif len(data_sources) >= 2:
        print("  ⚠️  数据部分完整 - 部分数据源有数据")
    else:
        print("  ⚠️  数据稀少 - 仅少量测试数据")

    print(f"\n  已启用数据源: {', '.join(data_sources)}")
else:
    print("  ⚠️  暂无真实数据 - 仅包含测试数据或空数据库")

print("\n" + "=" * 80)
print("验证完成")
print("=" * 80)

# 保存结果到JSON
report_path = Path("reports/lwm_data_volume_report.json")
report_path.parent.mkdir(exist_ok=True)

with open(report_path, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "results": results
    }, f, ensure_ascii=False, indent=2)

print(f"\n详细报告已保存至: {report_path}")
