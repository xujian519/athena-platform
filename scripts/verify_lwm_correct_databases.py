#!/usr/bin/env python3
"""
法律世界模型数据量验证脚本（正确版本）
Legal World Model Data Volume Verification (Correct Version)

连接到正确的数据库：legal_world_model
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
print("法律世界模型数据量验证（连接正确数据库）")
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

    URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024")

    print(f"  连接信息: {URI}")
    print(f"  用户名: {USERNAME}")

    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    # 先列出所有数据库
    with driver.session(database="system") as session:
        db_list = session.run("SHOW DATABASES").data()
        print(f"\n  可用数据库:")
        for db in db_list:
            db_name = db['name']
            db_status = db.get('currentStatus', 'unknown')
            print(f"    - {db_name}: {db_status}")

    # 连接到默认的neo4j数据库
    with driver.session(database="neo4j") as session:
        # 检查节点数量
        node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
        print(f"\n  ✅ 节点总数: {node_count:,}")

        # 检查关系数量
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        print(f"  ✅ 关系总数: {rel_count:,}")

        if node_count > 0:
            # 检查节点类型分布
            node_types = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
                LIMIT 20
            """)
            print("\n  节点类型分布（前20）:")
            for record in node_types:
                labels = record["labels"]
                count = record["count"]
                if labels:
                    label_str = ", ".join(labels)
                    print(f"    - {label_str}: {count:,}")

            # 检查关系类型分布
            rel_types = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
                LIMIT 20
            """)
            print("\n  关系类型分布（前20）:")
            for record in rel_types:
                rel_type = record["type"]
                count = record["count"]
                print(f"    - {rel_type}: {count:,}")

    driver.close()

    results["Neo4j"] = {
        "status": "✅ 正常",
        "nodes": node_count,
        "relationships": rel_count,
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

                if points_count > 0:
                    print(f"  ✅ {collection_name}: {points_count:,} 条 ({vector_size}维)")

        print(f"\n  ✅ 总数据点: {total_points:,}")

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
    import traceback
    traceback.print_exc()
    results["Qdrant"] = {
        "status": "❌ 失败",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 3. PostgreSQL 法律世界模型数据库（legal_world_model）
# ============================================================================
print("3. PostgreSQL 法律世界模型数据库（legal_world_model）")
print("-" * 80)

try:
    import psycopg2

    # 法律世界模型PostgreSQL配置
    PG_HOST = os.getenv("LWM_DB_HOST", "localhost")
    PG_PORT = os.getenv("LWM_DB_PORT", "5432")
    PG_USER = os.getenv("LWM_DB_USER", "postgres")
    PG_PASSWORD = os.getenv("LWM_DB_PASSWORD", "")
    PG_DATABASE = os.getenv("LWM_DB_NAME", "legal_world_model")

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

    # 检查数据库连接
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
        large_tables = []

        for schema, table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                count = cursor.fetchone()[0]
                total_rows += count
                table_details.append({"name": table, "rows": count})

                if count > 1000:
                    large_tables.append((table, count))
                    print(f"  ✅ {table}: {count:,} 行")
                elif count > 0:
                    print(f"  📊 {table}: {count:,} 行")

            except Exception as e:
                print(f"  ❌ {table}: 无法访问 ({e})")

        print(f"\n  ✅ 总记录数: {total_rows:,}")

        if large_tables:
            print(f"\n  主要数据表（>1000条）:")
            for table, count in sorted(large_tables, key=lambda x: x[1], reverse=True):
                print(f"    - {table}: {count:,} 行")

        results["PostgreSQL_LWM"] = {
            "status": "✅ 正常",
            "database": current_db,
            "tables": len(tables),
            "total_rows": total_rows,
            "large_tables": len(large_tables),
            "table_details": table_details,
            "has_data": total_rows > 0
        }
    else:
        print("  ⚠️  未找到数据表")
        results["PostgreSQL_LWM"] = {
            "status": "⚠️  无表",
            "has_data": False
        }

    cursor.close()
    conn.close()

except Exception as e:
    print(f"  ❌ PostgreSQL连接失败: {e}")
    import traceback
    traceback.print_exc()
    results["PostgreSQL_LWM"] = {
        "status": "❌ 失败",
        "error": str(e),
        "has_data": False
    }

print()

# ============================================================================
# 4. 数据量总结
# ============================================================================
print("=" * 80)
print("法律世界模型数据量总结")
print("=" * 80)

print(f"\n📊 数据库状态:")
print(f"  Neo4j知识图谱:       {results.get('Neo4j', {}).get('status', '未知')}")
print(f"  Qdrant向量数据库:     {results.get('Qdrant', {}).get('status', '未知')}")
print(f"  PostgreSQL法律知识库: {results.get('PostgreSQL_LWM', {}).get('status', '未知')}")

print(f"\n📈 数据量统计:")

total_data = 0
data_sources = []

# Neo4j
if "Neo4j" in results:
    neo4j_data = results["Neo4j"]
    if neo4j_data.get("has_data"):
        nodes = neo4j_data.get("nodes", 0)
        rels = neo4j_data.get("relationships", 0)
        print(f"\n  🔗 Neo4j知识图谱:")
        print(f"     - 节点总数:      {nodes:,}")
        print(f"     - 关系总数:      {rels:,}")
        total_data += nodes + rels
        data_sources.append("Neo4j")
    else:
        print(f"\n  ⚠️  Neo4j: 暂无数据")

# Qdrant
if "Qdrant" in results:
    qdrant_data = results["Qdrant"]
    if qdrant_data.get("has_data"):
        points = qdrant_data.get("total_points", 0)
        print(f"\n  🔍 Qdrant向量数据库:")
        print(f"     - 数据点总数:    {points:,}")
        total_data += points
        data_sources.append("Qdrant")
    else:
        print(f"\n  ⚠️  Qdrant: 暂无数据")

# PostgreSQL
if "PostgreSQL_LWM" in results:
    pg_data = results["PostgreSQL_LWM"]
    if pg_data.get("has_data"):
        rows = pg_data.get("total_rows", 0)
        tables = pg_data.get("tables", 0)
        print(f"\n  🗄️  PostgreSQL法律知识库:")
        print(f"     - 数据库:        {pg_data.get('database', 'N/A')}")
        print(f"     - 表数量:        {tables}")
        print(f"     - 记录总数:      {rows:,}")
        total_data += rows
        data_sources.append("PostgreSQL")
    else:
        print(f"\n  ⚠️  PostgreSQL: 暂无数据")

print(f"\n🎯 总体评估:")
if len(data_sources) >= 3:
    print("  ✅ 数据完整 - 所有数据源都有数据")
    completeness = "完整"
elif len(data_sources) >= 2:
    print("  ✅ 数据基本完整 - 大部分数据源有数据")
    completeness = "基本完整"
elif len(data_sources) >= 1:
    print("  ⚠️  数据部分缺失 - 部分数据源有数据")
    completeness = "部分缺失"
else:
    print("  ❌ 暂无数据 - 所有数据库均为空")
    completeness = "无数据"

print(f"\n  已启用数据源: {', '.join(data_sources) if data_sources else '无'}")
print(f"  总数据量估算: 约 {total_data:,} 条记录")

print("\n" + "=" * 80)
print("验证完成")
print("=" * 80)

# 保存结果到JSON
report_path = Path("reports/lwm_data_volume_correct.json")
report_path.parent.mkdir(exist_ok=True)

report_data = {
    "timestamp": datetime.now().isoformat(),
    "completeness": completeness,
    "total_data": total_data,
    "data_sources": data_sources,
    "results": results
}

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report_data, f, ensure_ascii=False, indent=2)

print(f"\n📄 详细报告已保存至: {report_path}")

# 返回完成状态
if len(data_sources) >= 2:
    print(f"\n✅ 法律世界模型数据验证通过")
    sys.exit(0)
else:
    print(f"\n⚠️  法律世界模型数据不完整")
    sys.exit(1)
