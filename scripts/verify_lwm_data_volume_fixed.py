#!/usr/bin/env python3
"""
法律世界模型数据量验证脚本（修正版）
Legal World Model Data Volume Verification (Fixed)

正确连接本地PostgreSQL和Neo4j的legal_world数据库
"""

import sys
from pathlib import Path
import os
from datetime import datetime
import json

# 设置路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("法律世界模型数据量验证（修正版）")
print("=" * 80)
print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 存储结果
results = {}

# ============================================================================
# 1. Neo4j 数据量检查（legal_world数据库）
# ============================================================================
print("1. Neo4j 知识图谱数据量（legal_world数据库）")
print("-" * 80)

try:
    from neo4j import GraphDatabase

    URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024")
    DATABASE = "legal_world"

    print(f"  连接信息: {URI}/{DATABASE}")
    print(f"  用户名: {USERNAME}")

    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    with driver.session(database=DATABASE) as session:
        # 检查节点数量
        node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
        print(f"\n  ✅ 节点总数: {node_count:,}")

        # 检查关系数量
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        print(f"  ✅ 关系总数: {rel_count:,}")

        # 检查节点类型分布
        node_types = session.run("""
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        print("\n  节点类型分布（前20）:")
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
            LIMIT 20
        """)
        print("\n  关系类型分布（前20）:")
        has_rels = False
        for record in rel_types:
            rel_type = record["type"]
            count = record["count"]
            print(f"    - {rel_type}: {count:,}")
            has_rels = True

        if not has_rels:
            print("    ⚠️  暂无关系数据")

        # 统计法律实体
        legal_entities = session.run("""
            MATCH (n:LegalEntity)
            RETURN count(n) as count
        """).single()["count"]
        print(f"\n  法律实体: {legal_entities:,}")

        # 统计法律关系
        legal_relations = session.run("""
            MATCH ()-[r:LEGAL_RELATION]->()
            RETURN count(r) as count
        """).single()["count"]
        print(f"  法律关系: {legal_relations:,}")

    driver.close()

    results["Neo4j"] = {
        "status": "✅ 正常",
        "database": DATABASE,
        "nodes": node_count,
        "relationships": rel_count,
        "legal_entities": legal_entities,
        "legal_relations": legal_relations,
        "has_data": node_count > 0
    }

except Exception as e:
    print(f"  ❌ Neo4j连接失败: {e}")
    import traceback
    traceback.print_exc()
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

    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    print(f"  连接信息: {QDRANT_URL}")

    # 获取所有集合
    response = requests.get(f"{QDRANT_URL}/collections")
    collections_data = response.json()

    if collections_data["status"] == "ok":
        collections = collections_data["result"]["collections"]
        print(f"\n  集合总数: {len(collections)}")

        total_points = 0
        total_vectors = 0
        collection_details = []

        for collection in collections:
            collection_name = collection["name"]
            # 获取集合详情
            detail_response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
            detail_data = detail_response.json()

            if detail_data["status"] == "ok":
                points_count = detail_data["result"]["points_count"]
                vectors_count = detail_data["result"]["vectors_count"]
                vector_size = detail_data["result"]["config"]["params"]["vectors"]["size"]
                total_points += points_count
                total_vectors += vectors_count

                collection_details.append({
                    "name": collection_name,
                    "points": points_count,
                    "vectors": vectors_count,
                    "vector_size": vector_size
                })

                print(f"  📦 {collection_name}:")
                print(f"     - 数据点: {points_count:,}")
                print(f"     - 向量数: {vectors_count:,}")
                print(f"     - 维度: {vector_size}")

        print(f"\n  ✅ 总数据点: {total_points:,}")
        print(f"  ✅ 总向量数: {total_vectors:,}")

        results["Qdrant"] = {
            "status": "✅ 正常",
            "collections": len(collections),
            "total_points": total_points,
            "total_vectors": total_vectors,
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
    import traceback
    traceback.print_exc()
    results["Qdrant"] = {
        "status": "❌ 失败",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 3. PostgreSQL 数据量检查（本地PostgreSQL）
# ============================================================================
print("3. PostgreSQL 结构化数据库数据量（本地）")
print("-" * 80)

try:
    import psycopg2

    # 本地PostgreSQL配置
    PG_HOST = "localhost"
    PG_PORT = 5432
    PG_USER = os.getenv("PG_USER", "xujian")  # 使用当前用户
    PG_PASSWORD = os.getenv("PG_PASSWORD", "")
    PG_DATABASE = os.getenv("PG_DATABASE", "athena")

    print(f"  连接信息: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    print(f"  用户: {PG_USER}")

    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DATABASE
    )

    cursor = conn.cursor()

    # 检查athena数据库是否存在
    cursor.execute("SELECT current_database()")
    current_db = cursor.fetchone()[0]
    print(f"  ✅ 连接成功: {current_db}")

    # 检查表是否存在
    cursor.execute("""
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)

    tables = cursor.fetchall()

    if tables:
        print(f"\n  数据表总数: {len(tables)}")
        print("\n  表数据量:")

        total_rows = 0
        table_details = []

        for schema, table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                count = cursor.fetchone()[0]
                total_rows += count
                table_details.append({"name": table, "rows": count})

                # 格式化输出
                if count > 0:
                    print(f"    ✅ {table}: {count:,} 行")
                else:
                    print(f"    ⚠️  {table}: 0 行")
            except Exception as e:
                print(f"    ❌ {table}: 无法访问 ({e})")

        print(f"\n  ✅ 总记录数: {total_rows:,}")

        results["PostgreSQL"] = {
            "status": "✅ 正常",
            "database": current_db,
            "tables": len(tables),
            "total_rows": total_rows,
            "table_details": table_details,
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
    print(f"  ❌ PostgreSQL连接失败: {e}")
    import traceback
    traceback.print_exc()
    results["PostgreSQL"] = {
        "status": "❌ 失败",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 4. 数据量总结
# ============================================================================
print("=" * 80)
print("数据量总结")
print("=" * 80)

print(f"\n📊 数据库状态:")
print(f"  Neo4j (legal_world):  {results.get('Neo4j', {}).get('status', '未知')}")
print(f"  Qdrant:               {results.get('Qdrant', {}).get('status', '未知')}")
print(f"  PostgreSQL (本地):    {results.get('PostgreSQL', {}).get('status', '未知')}")

print(f"\n📈 数据量统计:")

# Neo4j
if "Neo4j" in results:
    neo4j_data = results["Neo4j"]
    if neo4j_data.get("has_data"):
        print(f"\n  🔗 Neo4j知识图谱:")
        print(f"     - 节点总数:      {neo4j_data.get('nodes', 0):,}")
        print(f"     - 关系总数:      {neo4j_data.get('relationships', 0):,}")
        print(f"     - 法律实体:      {neo4j_data.get('legal_entities', 0):,}")
        print(f"     - 法律关系:      {neo4j_data.get('legal_relations', 0):,}")
    else:
        print(f"\n  ⚠️  Neo4j: 暂无数据")

# Qdrant
if "Qdrant" in results:
    qdrant_data = results["Qdrant"]
    if qdrant_data.get("has_data"):
        print(f"\n  🔍 Qdrant向量数据库:")
        print(f"     - 集合数量:      {qdrant_data.get('collections', 0)}")
        print(f"     - 数据点总数:    {qdrant_data.get('total_points', 0):,}")
        print(f"     - 向量总数:      {qdrant_data.get('total_vectors', 0):,}")
    else:
        print(f"\n  ⚠️  Qdrant: 暂无数据")

# PostgreSQL
if "PostgreSQL" in results:
    pg_data = results["PostgreSQL"]
    if pg_data.get("has_data"):
        print(f"\n  🗄️  PostgreSQL结构化数据库:")
        print(f"     - 数据库:        {pg_data.get('database', 'N/A')}")
        print(f"     - 表数量:        {pg_data.get('tables', 0)}")
        print(f"     - 记录总数:      {pg_data.get('total_rows', 0):,}")
    else:
        print(f"\n  ⚠️  PostgreSQL: 暂无数据")

print(f"\n🎯 总体评估:")
has_any_data = any(r.get("has_data", False) for r in results.values())

if has_any_data:
    # 统计有数据的数据库
    data_sources = [name for name, data in results.items() if data.get("has_data")]

    if len(data_sources) >= 3:
        print("  ✅ 数据完整 - 所有数据源都有数据")
        completeness = "完整"
    elif len(data_sources) >= 2:
        print("  ✅ 数据基本完整 - 大部分数据源有数据")
        completeness = "基本完整"
    else:
        print("  ⚠️  数据部分缺失 - 仅少量数据源有数据")
        completeness = "部分缺失"

    print(f"\n  已启用数据源: {', '.join(data_sources)}")

    # 计算总数据量
    total_data = 0
    if "Neo4j" in results and results["Neo4j"].get("has_data"):
        total_data += results["Neo4j"]["nodes"]
    if "Qdrant" in results and results["Qdrant"].get("has_data"):
        total_data += results["Qdrant"]["total_points"]
    if "PostgreSQL" in results and results["PostgreSQL"].get("has_data"):
        total_data += results["PostgreSQL"]["total_rows"]

    print(f"  总数据量估算: 约 {total_data:,} 条记录")

else:
    print("  ⚠️  暂无数据 - 所有数据库均为空")
    completeness = "无数据"

print("\n" + "=" * 80)
print("验证完成")
print("=" * 80)

# 保存结果到JSON
report_path = Path("reports/lwm_data_volume_report_fixed.json")
report_path.parent.mkdir(exist_ok=True)

report_data = {
    "timestamp": datetime.now().isoformat(),
    "completeness": completeness,
    "results": results
}

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, ensure_ascii=False, indent=2)

print(f"\n📄 详细报告已保存至: {report_path}")

# 返回完成状态
if has_any_data and len([r for r in results.values() if r.get("has_data")]) >= 2:
    sys.exit(0)
else:
    sys.exit(1)
