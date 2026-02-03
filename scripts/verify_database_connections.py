#!/usr/bin/env python3
"""
数据库连接验证脚本
Database Connection Verification Script

验证所有数据库连接是否正常工作。

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def verify_all_connections():
    """验证所有数据库连接"""
    print("=" * 80)
    print("数据库连接验证")
    print("=" * 80)
    print()

    results = {}

    # 1. 验证Neo4j
    print("【1】验证Neo4j连接...")
    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        import os

        load_dotenv()

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")

        driver = GraphDatabase.driver(uri, auth=(username, password))

        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]

        driver.close()

        print(f"  ✅ Neo4j连接成功！节点数: {count:,}")
        results["neo4j"] = True

    except Exception as e:
        print(f"  ❌ Neo4j连接失败: {e}")
        results["neo4j"] = False

    # 2. 验证PostgreSQL
    print("\n【2】验证PostgreSQL连接...")
    try:
        import psycopg2
        from dotenv import load_dotenv
        import os

        load_dotenv()

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "athena"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        )

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM patent_documents")
        doc_count = cur.fetchone()[0]

        cur.close()
        conn.close()

        print(f"  ✅ PostgreSQL连接成功！文档数: {doc_count:,}")
        results["postgres"] = True

    except Exception as e:
        print(f"  ❌ PostgreSQL连接失败: {e}")
        results["postgres"] = False

    # 3. 验证Redis
    print("\n【3】验证Redis连接...")
    try:
        import redis
        from dotenv import load_dotenv
        import os

        load_dotenv()

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD", "")

        r = redis.Redis(host=host, port=port, password=password, decode_responses=True)
        r.ping()

        info = r.info("stats")

        print(f"  ✅ Redis连接成功！")
        results["redis"] = True

    except Exception as e:
        print(f"  ❌ Redis连接失败: {e}")
        results["redis"] = False

    # 4. 验证Qdrant
    print("\n【4】验证Qdrant连接...")
    try:
        from qdrant_client import QdrantClient
        from dotenv import load_dotenv
        import os

        load_dotenv()

        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")

        client = QdrantClient(url=url, api_key=api_key)
        collections = client.get_collections()

        print(f"  ✅ Qdrant连接成功！集合数: {len(collections.collections)}")
        results["qdrant"] = True

    except Exception as e:
        print(f"  ❌ Qdrant连接失败: {e}")
        results["qdrant"] = False

    # 汇总报告
    print()
    print("=" * 80)
    print("验证报告")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"总计: {passed}/{total} 通过")

    for name, status in results.items():
        status_str = "✅ 通过" if status else "❌ 失败"
        print(f"  {name}: {status_str}")

    print()

    if passed == total:
        print("🎉 所有数据库连接正常！")
        return 0
    elif failed == 1:
        print("⚠️  部分连接失败，请检查配置")
        return 1
    else:
        print("❌ 多个连接失败，请立即检查")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(verify_all_connections())
    sys.exit(exit_code)
