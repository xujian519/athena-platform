#!/usr/bin/env python3
"""
法律世界模型启动与验证脚本 (简化版)
Legal World Model Startup and Verification (Simplified)

Author: Athena Team
Version: 1.0.0
Date: 2026-03-06
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def verify_databases():
    """验证数据库状态"""
    print("=" * 70)
    print("⚖️ 法律世界模型启动与验证")
    print("=" * 70)
    print()

    results = {}

    # 1. 检查PostgreSQL
    print("📊 PostgreSQL (本地)")
    print("-" * 70)
    try:
        import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="postgres",
            connect_timeout=5
        )
        cursor = conn.cursor()

        # 检查数据库
        cursor.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY pg_database_size(datname) DESC
            LIMIT 10
        """)
        databases = cursor.fetchall()

        # 检查表
        cursor.execute("""
            SELECT schemaname, COUNT(*) as table_count
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            GROUP BY schemaname
        """)
        schemas = cursor.fetchall()

        print("  ✅ 连接成功")
        print("  📦 主要数据库:")
        for db, size in databases[:5]:
            print(f"     - {db}: {size}")
        print("  📋 Schema表数量:")
        for schema, count in schemas[:5]:
            print(f"     - {schema}: {count} 个表")

        cursor.close()
        conn.close()

        results["postgresql"] = {"status": "connected", "databases": len(databases)}

    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        results["postgresql"] = {"status": "failed", "error": str(e)}

    print()

    # 2. 检查Qdrant
    print("🔍 Qdrant (持久化)")
    print("-" * 70)
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:6333/collections",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    collections = data.get("result", {}).get("collections", [])
                    print("  ✅ 连接成功")
                    print(f"  📦 集合数量: {len(collections)}")

                    for coll in collections[:5]:
                        print(f"     - {coll['name']}")

                    results["qdrant"] = {"status": "connected", "collections": len(collections)}
                else:
                    print(f"  ⚠️ 响应状态: {response.status}")
                    results["qdrant"] = {"status": "error", "code": response.status}

    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        results["qdrant"] = {"status": "failed", "error": str(e)}

    print()

    # 3. 检查Neo4j
    print("🕸️ Neo4j (持久化)")
    print("-" * 70)
    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "athena_neo4j_2024"),
        )

        async with driver.session() as session:
            # 检查节点
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            node_count = record["count"] if record else 0

            # 检查关系
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = await result.single()
            rel_count = record["count"] if record else 0

            # 检查标签
            result = await session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
            record = await result.single()
            labels = record["labels"] if record else []

            print("  ✅ 连接成功")
            print(f"  📊 节点数量: {node_count:,}")
            print(f"  🔗 关系数量: {rel_count:,}")
            print(f"  🏷️ 标签数量: {len(labels)}")

            for label in labels[:10]:
                print(f"     - {label}")

            results["neo4j"] = {
                "status": "connected",
                "nodes": node_count,
                "relationships": rel_count,
                "labels": len(labels)
            }

        await driver.close()

    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        results["neo4j"] = {"status": "failed", "error": str(e)}

    print()

    # 生成报告
    print("=" * 70)
    print("📊 法律世界模型状态报告")
    print("=" * 70)
    print()

    connected = sum([1 for v in results.values() if v.get("status") == "connected"])
    total = len(results)

    print(f"数据库总数: {total}")
    print(f"已连接: {connected}")
    print()

    for name, status in results.items():
        status_text = "✅ 已连接" if status.get("status") == "connected" else "❌ 未连接"
        print(f"{name.upper()}:\t{status_text}")

    print()

    if connected == total:
        print("✅ 法律世界模型已就绪，可以开始使用!")
    else:
        print("⚠️ 法律世界模型未完全就绪")

    # 保存报告
    report_path = Path("/Users/xujian/Athena工作平台/data/reports")
    report_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_path / f"法律世界模型验证报告_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"📄 报告已保存: {report_file}")

    return results


if __name__ == "__main__":
    try:
        asyncio.run(verify_databases())
    except KeyboardInterrupt:
        print("\n\n👋 验证已取消")
        sys.exit(0)
